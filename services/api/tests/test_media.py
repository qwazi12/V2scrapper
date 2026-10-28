from PIL import Image
from scos.media import card
from scos.config import RUNTIME


def test_selected_owner_image_is_used_in_frame():
    bg = RUNTIME / "selected-test-image.png"
    Image.new("RGB", (400, 400), (0, 230, 90)).save(bg)
    output = RUNTIME / "selected-card.png"
    card(output, (1080, 1350), "Owner story", "A clear visual promise.", 0, background=bg, fictional=False)
    with Image.open(output) as im:
        assert im.getpixel((540, 400)) == (0, 230, 90)
        assert im.size == (1080, 1350)
