from bs4 import BeautifulSoup

from urban_growth.scrapers.magicbricks import _parse_magicbricks_card, _summarize_page
from urban_growth.scrapers.municipal_pdf import _parse_pdf_text
from urban_growth.scrapers.ninetynineacres import _parse_99acres_card, _summarize_page as _summarize_99acres_page


def test_magicbricks_card_parsing_extracts_key_metrics() -> None:
    html = """
    <article>
      <a href="https://www.magicbricks.com/tarc-tripundra-bijwasan-new-delhi-pdpid-123">TARC Tripundra</a>
      <div>
        SUPER AREA 3200 sqft TRANSACTION New Property FURNISHING Unfurnished
        Read more₹9.85 Cr ₹30,781 per sqft Properties (27092)
      </div>
    </article>
    """
    soup = BeautifulSoup(html, "html.parser")
    page_summary = _summarize_page(soup)
    record = _parse_magicbricks_card(soup.article, "https://www.magicbricks.com/property-for-sale/residential-real-estate?cityName=New-Delhi", "Delhi NCR", page_summary)

    assert record is not None
    assert record["price_psf_current"] == 30781.0
    assert record["listing_density"] == 27092.0
    assert record["declaration_type"] == "MagicBricks New Property"


def test_99acres_card_parsing_extracts_key_metrics() -> None:
    html = """
    <article>
      <a href="https://www.99acres.com/property-details">Luxury Apartment in New Delhi</a>
      <div>
        Delhi NCR Ready to Move ₹1.25 Cr ₹12,500 per sqft 88246+ Apartments / Flats for Sale in Delhi / NCR
      </div>
    </article>
    """
    soup = BeautifulSoup(html, "html.parser")
    page_summary = _summarize_99acres_page(soup)
    record = _parse_99acres_card(soup.article, "https://www.99acres.com/flats-in-delhi-ncr-ffid", "Delhi NCR", page_summary)

    assert record is not None
    assert record["price_psf_current"] == 12500.0
    assert record["listing_density"] == 88246.0
    assert record["declaration_type"] == "99acres Ready to Move"


def test_municipal_pdf_parser_uses_public_infrastructure_keywords() -> None:
    text = """
    MUNICIPAL CORPORATION OF DELHI
    Press Note for Delimitation of Wards for the Municipal Corporation of Delhi
    Dated 12/09/2022
    Ward 12 Metro Corridor expansion and drainage modernization
    latitude: 28.63 longitude: 77.21
    """

    record = _parse_pdf_text(text, "https://sec.delhi.gov.in/sites/default/files/SEC/generic_multiple_files/press_note_for_delimitation_of_wards_for_the_municipal_corporation_of_delhi.pdf", "Delhi NCR")

    assert record["city"] == "Delhi NCR"
    assert record["infra_impact_score"] >= 90.0
    assert "Ward" in record["zone"]
    assert record["announced_date"] == "12/09/2022"
