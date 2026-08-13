import pytest

from backend.core import Kernel
from backend.engines.seo import SeoContribution, SeoEngine, SeoMetadata, SeoResourceContext, SeoSource
from backend.engines.seo.engine import InvalidSeo


def test_seo_precedence_fallback_update_and_private_visibility(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.seo", SeoEngine); public = {"one": True}
    engine.register_resource_type("content", owner="content", is_public=lambda resource_id: public.get(resource_id, False))
    context = SeoResourceContext("content", "one")
    engine.set(SeoContribution(context, "platform", SeoSource.PLATFORM_DEFAULT, SeoMetadata(title="Default", description="Default description")))
    engine.set(SeoContribution(context, "content", SeoSource.RESOURCE, SeoMetadata(title="Resource")))
    resolved = engine.resolve(context); assert resolved.title == "Resource" and resolved.description == "Default description"
    engine.set(SeoContribution(context, "content", SeoSource.RESOURCE, SeoMetadata(title="Updated")))
    assert engine.resolve(context).title == "Updated"
    public["one"] = False
    assert engine.resolve(context) == SeoMetadata()


def test_seo_canonical_validation_and_source_removal(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.seo", SeoEngine); engine.register_resource_type("content", owner="content", is_public=lambda resource_id: True)
    context = SeoResourceContext("content", "two")
    with pytest.raises(InvalidSeo): SeoContribution(context, "content", SeoSource.EXPLICIT, SeoMetadata(canonical="file:///private/path"))
    contribution = SeoContribution(context, "content", SeoSource.EXPLICIT, SeoMetadata(canonical="https://example.com/page"))
    engine.set(contribution); assert engine.resolve(context).canonical == "https://example.com/page"
    engine.remove(context, owner="content", source=SeoSource.EXPLICIT); assert engine.resolve(context).canonical is None
