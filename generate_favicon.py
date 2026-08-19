from PIL import Image

# Load source image
src = 'static/jkpv-store.png'
out = 'static/favicon.ico'

try:
    im = Image.open(src)
    # Ensure RGBA
    im = im.convert('RGBA')
    # Make square by padding
    size = max(im.size)
    new_im = Image.new('RGBA', (size, size), (255,255,255,0))
    new_im.paste(im, ((size - im.width)//2, (size - im.height)//2))
    # Resize to standard favicon sizes
    icons = []
    for s in (16, 32, 48, 64):
        icons.append(new_im.resize((s, s), Image.LANCZOS))
    # Save as .ico with multiple sizes
    icons[0].save(out, format='ICO', sizes=[(s,s) for s in (16,32,48,64)])
    print('favicon created:', out)
except Exception as e:
    print('Error creating favicon:', e)
