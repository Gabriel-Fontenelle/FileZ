import pytest

from filejacket import File

from .data.images import DATA_DIR as IMAGE_DATA_DIR
from .data.videos import DATA_DIR as VIDEO_DATA_DIR
from .data.packets import DATA_DIR as PACKET_DATA_DIR


@pytest.fixture
def file_jpg():
    return File(path=f"{IMAGE_DATA_DIR}/aurora-1197753_1280_by_Noel_Bauza_at_pixabay.jpg")


@pytest.fixture
def file_png():
    return File(path="")


@pytest.fixture
def file_psd():
    return File(path=f"{PACKET_DATA_DIR}/3763816_76417.psd")


@pytest.fixture
def file_gif():
    return File(path=f"{IMAGE_DATA_DIR}/snow-man-10450_by_winterflower_at_pixabay.gif")


@pytest.fixture
def file_svg():
    return File(path=f"{IMAGE_DATA_DIR}/watermelon-8368960_by_ebengg_at_pixabay.svg")


@pytest.fixture
def file_epub():
    return File(path=f"{PACKET_DATA_DIR}/franklin-w-dixon_hunting-for-hidden-gold_advanced.epub")


@pytest.fixture
def file_rar():
    return File(path=f"{PACKET_DATA_DIR}/images.rar")


@pytest.fixture
def file_tar():
    return File(path=f"{PACKET_DATA_DIR}/images.tar")


@pytest.fixture
def file_7zip():
    return File(path=f"{PACKET_DATA_DIR}/images.7z")


@pytest.fixture
def file_zip():
    return File(path=f"{PACKET_DATA_DIR}/images.zip")


@pytest.fixture
def file_cbz():
    return File(path=f"{PACKET_DATA_DIR}/images.cbz")


@pytest.fixture
def file_mp4():
    return File(path=f"{VIDEO_DATA_DIR}/183136-870151786_small_by_setfwithanf_At_pixabay.mp4")
