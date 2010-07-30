#!BPY

"""
Name: 'ML3D (.ml3d)'
Blender: 249
Group: 'Export'
Tooltip: 'ml3d format model exporter'
"""

import Blender, struct, os, math

# Header format:
# uint32 - ident: 0x4D4C3344 (ML3D in big-endian)
# uint32 - version: 1
# uint32 - vert_offset
# uint32 - edge_offset
# uint32 - face_offset
# uint32 - vertlist_offset
# uint32 - edgelist_offset
# uint32 - num_verts
# uint32 - num_edges
# uint32 - num_faces
# uint32 - num_vertlist
# uint32 - num_edgelist
header_struct = ">IIIIIIIIIIII"
header_size   = struct.calcsize(header_struct)

# Vert: float x, y, z
vert_struct   = ">fff"
vert_size     = struct.calcsize(vert_struct)

# Edge: 
# uint16 verts[2]
# uint16 faces[2] -- 0xFFFF = null
edge_struct   = ">HHHH"
edge_size     = struct.calcsize(edge_struct)

# Face:
# uint32 vertlist
# uint32 edgelist
# uint8  num_verts
# uint8  num_edges
#  int8  theta, phi -- normal data in spherical coords
face_struct   = ">IIBBbb"
face_size     = struct.calcsize(face_struct)

vertlist_struct = ">H"
vertlist_size   = struct.calcsize(vertlist_struct)

edgelist_struct = ">H"
edgelist_size   = struct.calcsize(edgelist_struct)

def export(path):
	buf = file(path, 'w')
	buf.write("\0"*header_size)

	objects = Blender.Object.GetSelected()
	if len(objects) != 1:
		Blender.Draw.PupMenu("Error: Select exactly one mesh!%t|OK")
		return
	mesh = objects[0].getData(mesh=True)

	edge_faces   = {}
	edge_indexes = {}
	for edge_idx, edge in zip(range(len(mesh.edges)), mesh.edges):
		edge_faces[edge.key]   = []
		edge_indexes[edge.key] = edge_idx
	for face_idx, face in zip(range(len(mesh.faces)), mesh.faces):
		for edge_key in face.edge_keys:
			edge_faces[edge_key].append(face_idx)
	
	header = {
		'ident'   : 0x4D4C3344,
		'version' : 1
	}
	
	offset = 0
	header['num_verts']   = len(mesh.verts)
	header['vert_offset'] = offset
	for vert in mesh.verts:
		buf.write(struct.pack(vert_struct, vert.co.x, vert.co.y, vert.co.z))
		offset += vert_size
	
	header['num_edges']   = len(mesh.edges)
	header['edge_offset'] = offset
	for edge in mesh.edges:
		faces = [
			0xFFFF,
			0xFFFF
		]
		try:
			faces[0] = edge_faces[edge.key][0]
		except:
			faces[0] = 0xFFFF
		try:
			faces[1] = edge_faces[edge.key][1]
		except:
			faces[1] = 0xFFFF
		buf.write(struct.pack(edge_struct, edge.v1.index, edge.v2.index, faces[0], faces[1]))
		offset += edge_size
	
	vertlist_buf = ""
	edgelist_buf = ""
	vertlist_idx = 0
	edgelist_idx = 0
	header['num_faces']   = len(mesh.faces)
	header['face_offset'] = offset
	for face in mesh.faces:
		theta = int(127.0*math.acos(face.no.z)/math.pi)
		phi   = int(127.0*math.atan2(face.no.y, face.no.x)/math.pi)
		buf.write(struct.pack(face_struct, vertlist_idx, edgelist_idx, len(face.verts), len(face.edge_keys), theta, phi))
		offset += face_size
		for vert in face.verts:
			vertlist_buf += struct.pack(vertlist_struct, vert.index)
			vertlist_idx += 1
		for edge_key in face.edge_keys:
			edgelist_buf += struct.pack(edgelist_struct, edge_indexes[edge_key])
			edgelist_idx += 1
	
	header['num_vertlist']    = vertlist_idx
	header['vertlist_offset'] = offset
	buf.write(vertlist_buf)
	offset += len(vertlist_buf)

	header['num_edgelist']    = edgelist_idx
	header['edgelist_offset'] = offset
	buf.write(edgelist_buf)

	header = struct.pack(header_struct, header['ident'], header['version'], header['vert_offset'], header['edge_offset'], header['face_offset'], header['vertlist_offset'], header['edgelist_offset'],
	            header['num_verts'], header['num_edges'], header['num_faces'], header['num_vertlist'], header['num_edgelist'])
	buf.seek(0, os.SEEK_SET)
	buf.write(header)

	buf.close()

Blender.Window.FileSelector(export, "Export")
