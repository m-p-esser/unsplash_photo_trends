from dataclasses import dataclass

from dataclasses_json import Undefined, dataclass_json


@dataclass_json
@dataclass(slots=True)
class EXIF:
    """Cameria EXIF data"""

    make: str
    model: str
    name: str
    exposure_time: str
    aperture: float
    focal_length: float
    iso: int


@dataclass_json
@dataclass(slots=True)
class Position:
    """Latitude and Longitude coordinates"""

    latitude: float
    longitude: float


@dataclass_json
@dataclass(slots=True)
class Location:
    """Name, City, Country and Position of a Location"""

    name: str
    city: str
    country: str
    position: Position


@dataclass_json
@dataclass(slots=True)
class RawImageURLs:
    """URLs leading to image with different resolutions"""

    raw: str
    full: str
    regular: str
    small: str
    thumb: str
    small_s3: str


@dataclass_json
@dataclass(slots=True)
class MiscImageURLs:
    """URLs leading to download and original html"""

    self: str
    html: str
    download: str
    download_location: str


@dataclass_json
@dataclass(slots=True)
class MiscUserURLs:
    """URLs leading to different links related to a User, e.g. follower"""

    self: str
    html: str
    photos: str
    likes: str
    portfolio: str
    following: str
    followers: str


@dataclass_json
@dataclass(slots=True)
class UserProfileImageURLs:
    """URLs leading to image with different resolutions of User Profile image"""

    small: str
    medium: str
    large: str


@dataclass_json
@dataclass(slots=True)
class UserSocial:
    """Social contact information"""

    instagram_username: str
    portfolio_url: str
    twitter_username: str
    paypal_email: str


@dataclass_json
@dataclass(slots=True)
class User:
    """All User related data"""

    id: str
    updated_at: str
    username: str
    name: str
    first_name: str
    last_name: str
    twitter_username: str
    portfolio_url: str
    bio: str
    location: str
    links: MiscUserURLs
    profile_image: UserProfileImageURLs
    instagram_username: str
    total_collections: int
    total_likes: int
    total_photos: int
    accepted_tos: bool
    for_hire: bool
    social: UserSocial


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PhotoEditorialMetadataExpanded:
    """Photo metadata class"""

    id: str
    slug: str
    created_at: str
    updated_at: str
    promoted_at: str
    width: int
    height: int
    color: str
    blur_hash: str
    description: str
    alt_description: str
    urls: RawImageURLs
    links: MiscImageURLs
    likes: int
    premium: bool
    plus: bool
    user: User
    exif: EXIF
    location: Location
    views: int
    downloads: int
    requested_at: str
