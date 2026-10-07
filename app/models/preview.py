"""Kontrak respons GET /preview/{id}. Cerminan src/types.ts di frontend: ubah keduanya bersamaan."""
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Img(BaseModel):
    url: str
    alt: str = ""

class Hours(BaseModel):
    days: str
    open: str

class Product(BaseModel):
    id: str
    name: str
    price: int | None = Field(None, ge=0)
    category: str | None = None
    description: str | None = None
    image: Img | None = None
    suggested: bool = False

class Business(BaseModel):
    name: str
    category: str
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    whatsapp: str
    bio: str | None = None
    hours: list[Hours] = Field(default_factory=list)
    logo: Img | None = None
    products: list[Product] = Field(default_factory=list)

# ---- offering (tiga varian) ----
class Catalog(BaseModel):
    kind: Literal["catalog"] = "catalog"
    title: str
    product_ids: list[str]
    suggested: bool = False

class Tier(BaseModel):
    name: str
    price: int | None = Field(None, ge=0)
    features: list[str] = Field(default_factory=list, max_length=6)
    featured: bool = False

class Packages(BaseModel):
    kind: Literal["packages"] = "packages"
    title: str
    tiers: list[Tier] = Field(max_length=4)
    suggested: bool = False

class Service(BaseModel):
    name: str
    description: str
    icon: str | None = None

class Services(BaseModel):
    kind: Literal["services"] = "services"
    title: str
    items: list[Service] = Field(max_length=8)
    suggested: bool = False

class Event(BaseModel):
    name: str
    date: str | None = None
    time: str | None = None
    place: str | None = None
    description: str | None = None

class Events(BaseModel):
    kind: Literal["events"] = "events"
    title: str
    items: list[Event] = Field(max_length=4)
    suggested: bool = False

Offering = Annotated[Union[Catalog, Packages, Services, Events], Field(discriminator="kind")]

# ---- situs ----
class Theme(BaseModel):
    primary: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    background: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    ink: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")

class Hero(BaseModel):
    headline: str
    subheadline: str
    cta_label: str
    image: Img | None = None

class Positioning(BaseModel):
    title: str
    body: str
    points: list[str] = Field(default_factory=list, max_length=3)
    suggested: bool = False

class Proof(BaseModel):
    title: str
    facts: list[str] = Field(default_factory=list, max_length=4)
    photos: list[Img] = Field(default_factory=list, max_length=6)
    suggested: bool = False

class Cta(BaseModel):
    headline: str
    body: str
    label: str

class Site(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    theme: Theme
    hero: Hero
    positioning: Positioning
    offering: Offering | None = None
    proof: Proof | None = None
    cta: Cta

# ---- kanal ----
class CopyText(BaseModel):
    title: str
    body: str

class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    priority: Literal["primary", "high", "supporting"]
    reason: str
    copy_: CopyText | None = Field(None, alias="copy")  # "copy" bentrok dengan BaseModel.copy

class Rating(BaseModel):
    value: float = Field(ge=0, le=5)
    count: int | None = None
    sample: bool = False

class GoogleData(BaseModel):
    photos: list[Img] = Field(default_factory=list, max_length=8)
    rating: Rating | None = None

class Highlight(BaseModel):
    label: str
    icon: str
    kind: Literal["menu", "location", "contact", "text"]
    title: str | None = None
    body: str | None = None
    image: Img | None = None

class Post(BaseModel):
    image: Img
    caption: str

class InstagramData(BaseModel):
    handle: str
    suggested: bool = False
    highlights: list[Highlight] = Field(default_factory=list, max_length=5)
    posts: list[Post] = Field(max_length=9)

class MarketplaceData(BaseModel):
    platform: Literal["shopee", "tokopedia"]
    store_name: str
    product_ids: list[str]

class WebsitePresence(_Base):
    type: Literal["website"] = "website"

class GooglePresence(_Base):
    type: Literal["google_business"] = "google_business"
    data: GoogleData

class InstagramPresence(_Base):
    type: Literal["instagram"] = "instagram"
    data: InstagramData

class MarketplacePresence(_Base):
    type: Literal["marketplace"] = "marketplace"
    data: MarketplaceData

Presence = Annotated[Union[WebsitePresence, GooglePresence, InstagramPresence, MarketplacePresence], Field(discriminator="type")]

# ---- envelope ----
class Ready(BaseModel):
    status: Literal["ready"] = "ready"
    job_id: str
    consult_whatsapp: str  # nomor tim Langsung Online (tombol konsultasi)
    business: Business
    site: Site
    recommended_presence: list[Presence] = Field(min_length=1)
    recommendations: list[str] = Field(min_length=2, max_length=4)
    completeness: Literal["rich", "basic", "minimal"] | None = None

    @model_validator(mode="after")
    def _cross_check(self):
        ids = {p.id for p in self.business.products}
        if isinstance(self.site.offering, Catalog) and not set(self.site.offering.product_ids) <= ids:
            raise ValueError("offering.product_ids merujuk ke produk yang tidak ada")
        kinds = [p.type for p in self.recommended_presence]
        if kinds[0] != "website":
            raise ValueError("website harus kanal pertama")
        if len(kinds) != len(set(kinds)):
            raise ValueError("tipe kanal tidak boleh ganda")
        for p in self.recommended_presence:
            if isinstance(p, MarketplacePresence) and not set(p.data.product_ids) <= ids:
                raise ValueError("marketplace.product_ids merujuk ke produk yang tidak ada")
        return self

class NeedsInfo(BaseModel):
    status: Literal["needs_info"] = "needs_info"
    job_id: str
    question: str

class Simple(BaseModel):
    status: Literal["processing", "failed", "declined"]
    job_id: str

PreviewResponse = Annotated[Union[Ready, NeedsInfo, Simple], Field(discriminator="status")]
