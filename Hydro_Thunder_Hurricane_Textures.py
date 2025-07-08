from inc_noesis import *

# Rotates RGBA image data 90 degrees clockwise
def rotate_90_cw(pixel_data, width, height):
    new_pixel_data = bytearray(len(pixel_data))
    for y in range(height):
        for x in range(width):
            new_x, new_y = height - 1 - y, x
            src_idx = (y * width + x) * 4
            dst_idx = (new_y * width + new_x) * 4
            new_pixel_data[dst_idx:dst_idx+4] = pixel_data[src_idx:src_idx+4]
    return new_pixel_data

# Rotates RGBA image data 180 degrees
def rotate_180(pixel_data, width, height):
    new_pixel_data = bytearray(len(pixel_data))
    for y in range(height):
        for x in range(width):
            new_x, new_y = width - 1 - x, height - 1 - y
            src_idx = (y * width + x) * 4
            dst_idx = (new_y * width + new_x) * 4
            new_pixel_data[dst_idx:dst_idx+4] = pixel_data[src_idx:src_idx+4]
    return new_pixel_data

# Rotates RGBA image data 270 degrees clockwise
def rotate_270_cw(pixel_data, width, height):
    new_pixel_data = bytearray(len(pixel_data))
    for y in range(height):
        for x in range(width):
            new_x, new_y = y, width - 1 - x
            src_idx = (y * width + x) * 4
            dst_idx = (new_y * width + new_x) * 4
            new_pixel_data[dst_idx:dst_idx+4] = pixel_data[src_idx:src_idx+4]
    return new_pixel_data

# Register this script as a Noesis plugin
def registerNoesisTypes():
    handle = noesis.register("Hydro Thunder Hurricane (XBox 360) - Textures", ".bin")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadRGBA(handle, LoadRGBA)
    return 1

# Basic check to verify the file is valid
def CheckType(data):
    if len(data) < 16:
        return 0
    return 1

# Get the byte size of a block for a given DXT format
def get_dxt_block_size(tex_type):
    if tex_type in [0x152, 0x153]: return 8   # DXT1 / DXT3
    elif tex_type in [0x154, 0x171]: return 16  # DXT5 / BC5
    return 0

# Load a single 2D texture from the stream
def load_2d_texture(bs, texList):
    bs.seek(0)
    width = bs.readUInt()
    height = bs.readUInt()
    mip_count = bs.readUInt()
    unk1 = bs.readUShort()
    tex_type = bs.readUShort()
    data_size = bs.readUInt()

    # Fix mip count if it's stored in the alternate field
    if mip_count == 1 and unk1 > 1:
        mip_count = unk1

    pixel_data = bs.readBytes(data_size)

    # Handle DXT-compressed formats
    if tex_type in [0x152, 0x153, 0x154, 0x171]:
        block_bytes = get_dxt_block_size(tex_type)
        dxt_format = (
            noesis.NOESISTEX_DXT1 if tex_type in [0x152, 0x153]
            else noesis.NOESISTEX_DXT5 if tex_type == 0x154
            else noesis.NOESISTEX_ATI2
        )
        swapped = rapi.swapEndianArray(pixel_data, 2)
        untiled = rapi.imageUntile360DXT(swapped, width, height, block_bytes)
        texList.append(NoeTexture("texture_2d", width, height, untiled, dxt_format))
    else:
        # Unsupported or unimplemented format
        return 0
    return 1

# Load and process a cubemap texture
def load_cube_texture(bs, texList, width):
    height = width  # Cubemap faces are square

    bs.seek(8)
    format_flags = bs.readUInt()
    tex_type = format_flags & 0xFFFF
    bs.seek(16)

    print("Texture Type: Cube Map | Dimensions: " + str(width) + "x" + str(height))

    block_bytes = get_dxt_block_size(tex_type)
    if block_bytes == 0:
        return 0

    face_size = (width // 4) * (height // 4) * block_bytes
    decoded_faces = []

    # Read and decode all 6 faces
    for i in range(6):
        face_data = bs.readBytes(face_size)
        swapped = rapi.swapEndianArray(face_data, 2)
        untiled = rapi.imageUntile360DXT(swapped, width, height, block_bytes)
        rgba_face = rapi.imageDecodeDXT(untiled, width, height, noesis.FOURCC_BC1)
        decoded_faces.append(rgba_face)

    # Fix orientation of each face
    print("Correcting face orientations...")
    face_px = rotate_90_cw(decoded_faces[0], width, height)
    face_nx = rotate_270_cw(decoded_faces[1], width, height)
    face_py = decoded_faces[3]
    face_ny = rotate_180(decoded_faces[2], width, height)
    face_pz = rotate_270_cw(decoded_faces[4], width, height)
    face_nz = rotate_270_cw(decoded_faces[5], width, height)

    # Order the corrected faces into standard layout
    standard_order_faces = [face_px, face_nx, face_py, face_ny, face_pz, face_nz]

    # Add each face to the texture list
    for i in range(6):
        tex_name = "cubemap_face_" + str(i)
        tex = NoeTexture(tex_name, width, height, standard_order_faces[i], noesis.NOESISTEX_RGBA32)
        texList.append(tex)

    return 1

# Main function that determines whether to load a 2D texture or cubemap
def LoadRGBA(data, texList):
    noesis.logPopup()
    bs = NoeBitStream(data, NOE_BIGENDIAN)

    # Check type byte at offset 0xD to determine format
    bs.seek(0xD)
    type_byte = bs.readUByte()
    bs.seek(0)

    if type_byte == 0x03:
        return load_cube_texture(bs, texList, 128)
    elif type_byte == 0x06:
        return load_cube_texture(bs, texList, 256)
    else:
        return load_2d_texture(bs, texList)
