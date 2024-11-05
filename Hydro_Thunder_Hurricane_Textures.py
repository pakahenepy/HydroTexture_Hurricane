from inc_noesis import *

def registerNoesisTypes():
    handle = noesis.register("Hydro Thunder Hurricane (XBox 360) - Textures", ".bin")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadRGBA(handle, LoadRGBA)
    return 1

# Check file type
def CheckType(data):
    bs = NoeBitStream(data)
    return 1

def LoadRGBA(data, texList):
    bs = NoeBitStream(data, NOE_BIGENDIAN)

    # Read header data
    width = bs.readUInt()
    height = bs.readUInt()
    mip_count = bs.readUInt()
    unk1 = bs.readUShort()
    type = bs.readUShort()
    data_size = bs.readUInt()

    print("Type:\t", hex(type))
    print("Width:", width, "Height:", height, "Data Size:", data_size)

    # Read the raw image data
    raw_image = bs.readBytes(data_size)

    if type == 0x102:
        raw_image = rapi.imageUntile360Raw(raw_image, width, height, 1)
        raw_image = rapi.imageDecodeRaw(raw_image, width, height, "R8")

        # Expand R8 data to RGBA format
        rgba_image = bytearray()
        for r in raw_image:
            rgba_image.extend((r, r, r, 255))  # Duplicate R to G and B, set A to 255

    elif type == 0x152:
        raw_image = rapi.swapEndianArray(raw_image, 2)
        raw_image = rapi.imageUntile360DXT(raw_image, width, height, 8)
        raw_image = rapi.imageDecodeDXT(raw_image, width, height, noesis.FOURCC_BC1)
    elif type == 0x154:
        raw_image = rapi.swapEndianArray(raw_image, 2)
        raw_image = rapi.imageUntile360DXT(raw_image, width, height, 16)
        raw_image = rapi.imageDecodeDXT(raw_image, width, height, noesis.FOURCC_BC3)
    elif type == 0x171:
        raw_image = rapi.swapEndianArray(raw_image, 2)
        raw_image = rapi.imageUntile360DXT(raw_image, width, height, 16)
        raw_image = rapi.imageDecodeDXT(raw_image, width, height, noesis.FOURCC_BC5)
    elif type == 0x186:
        # Assuming 0x186 is R8G8B8A8 typeless, untile as 32-bit data and swap endianness
        raw_image = rapi.imageUntile360Raw(raw_image, width, height, 4)
        raw_image = rapi.swapEndianArray(raw_image, 4)  # Swap every 4 bytes
        raw_image = rapi.imageDecodeRaw(raw_image, width, height, "B8G8R8A8")
    else:
        print("Unknown type:\t", hex(type))
        return 0

    # Append texture to texList with RGBA format
    texList.append(NoeTexture("Image1", width, height, raw_image, noesis.NOESISTEX_RGBA32))

    return 1
