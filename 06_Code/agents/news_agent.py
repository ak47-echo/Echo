import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


DEFAULT_NEWS_SOURCES = (
    {
        "name": "Federal Reserve",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "official": True
    },
    {
        "name": "SEC",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "official": True
    },
    {
        "name": "BLS",
        "url": "https://www.bls.gov/feed/bls_latest.rss",
        "official": True
    },
    {
        "name": "BEA",
        "url": "https://apps.bea.gov/rss/rss.xml",
        "official": True
    },
    {
        "name": "CNBC Markets",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "official": False
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "official": False
    }
)

# TODO: Replace static portfolio/watchlist term lists with dynamic
# holdings/watchlist integration in a future phase.
PORTFOLIO_TERMS = (
    "UNH",
    "UnitedHealth",
    "UnitedHealth Group",
    "SMCI",
    "Super Micro",
    "Super Micro Computer",
    "IBIT",
    "Bitcoin",
    "BTC",
    "MSTR",
    "MicroStrategy",
    "Strategy",
    "ECO",
    "Okeanis",
    "Okeanis Eco Tankers",
    "VNOM",
    "Viper Energy",
    "SCHG",
    "SCHA",
    "SCHF",
    "SPYM",
    "QMOM"
)

WATCHLIST_TERMS = (
    "AVUV",
    "AVDV",
    "SGOV",
    "Treasury ETF",
    "short-term Treasury"
)

MACRO_TERMS = (
    "Fed",
    "Federal Reserve",
    "FOMC",
    "Powell",
    "interest rates",
    "rate cut",
    "rate hike",
    "inflation",
    "CPI",
    "PPI",
    "jobs",
    "payrolls",
    "unemployment",
    "GDP",
    "recession",
    "soft landing",
    "yield curve",
    "Treasury yields",
    "dollar",
    "credit spreads"
)

MARKET_TERMS = (
    "S&P 500",
    "Nasdaq",
    "Dow",
    "Russell 2000",
    "equities",
    "stocks",
    "bonds",
    "yields",
    "earnings",
    "guidance",
    "valuation",
    "volatility",
    "selloff",
    "rally"
)

WORLD_EVENT_TERMS = (
    "war",
    "conflict",
    "attack",
    "sanctions",
    "tariffs",
    "oil shock",
    "supply chain",
    "election",
    "cyberattack",
    "shutdown",
    "default",
    "debt ceiling",
    "geopolitical",
    "Middle East",
    "China",
    "Taiwan",
    "Russia",
    "Ukraine",
    "Israel",
    "Iran"
)

HEALTHCARE_TERMS = (
    "healthcare",
    "health insurance",
    "Medicare",
    "Medicaid",
    "drug pricing",
    "hospital",
    "insurer"
)

AI_SEMICONDUCTOR_TERMS = (
    "AI",
    "artificial intelligence",
    "semiconductor",
    "chips",
    "Nvidia",
    "data center",
    "server",
    "GPU"
)

ENERGY_TERMS = (
    "oil",
    "crude",
    "OPEC",
    "tanker",
    "shipping",
    "LNG",
    "natural gas",
    "energy"
)

CRYPTO_TERMS = (
    "bitcoin",
    "crypto",
    "ETF",
    "digital asset"
)

URGENCY_TERMS = (
    "breaking",
    "emergency",
    "unexpected",
    "surprise",
    "warning",
    "downgrade",
    "upgrade",
    "investigation",
    "lawsuit",
    "bankruptcy",
    "acquisition",
    "merger",
    "beats",
    "misses",
    "cuts forecast",
    "raises forecast",
    "plunges",
    "surges"
)

REGULATORY_TERMS = (
    "regulation",
    "regulatory",
    "SEC",
    "enforcement",
    "rule",
    "lawsuit",
    "investigation"
)

EARNINGS_TERMS = (
    "earnings",
    "guidance",
    "beats",
    "misses",
    "cuts forecast",
    "raises forecast"
)

RATES_TERMS = (
    "interest rates",
    "rate cut",
    "rate hike",
    "Treasury yields",
    "yield curve",
    "yields"
)

TAG_ORDER = (
    "PORTFOLIO",
    "WATCHLIST",
    "MACRO",
    "MARKET",
    "WORLD_EVENT",
    "REGULATORY",
    "EARNINGS",
    "CENTRAL_BANK",
    "ENERGY",
    "AI_SEMICONDUCTOR",
    "HEALTHCARE",
    "CRYPTO",
    "RATES",
    "UNKNOWN"
)

IMPACT_TIER_RANK = {
    "CRITICAL": 5,
    "HIGH": 4,
    "ELEVATED": 3,
    "MODERATE": 2,
    "LOW": 1
}

MEGA_CAP_TERMS = (
    "Apple",
    "Microsoft",
    "Nvidia",
    "Amazon",
    "Alphabet",
    "Google",
    "Meta",
    "Tesla",
    "Broadcom",
    "Berkshire",
    "Eli Lilly",
    "JPMorgan",
    "Exxon",
    "Netflix",
    "AMD",
    "Oracle"
)

HIGH_IMPACT_MODIFIERS = (
    "shock",
    "surprise",
    "unexpected",
    "hotter",
    "cooler",
    "accelerates",
    "slows",
    "plunges",
    "surges",
    "cuts",
    "hikes",
    "warns",
    "warning",
    "crisis",
    "stress",
    "default",
    "liquidity",
    "emergency",
    "escalates",
    "attack",
    "war"
)

ROUTINE_RELEASE_TERMS = (
    "latest numbers",
    "latest estimates",
    "monthly report",
    "weekly report",
    "routine",
    "schedule",
    "release",
    "releases",
    "statistics",
    "data update"
)

VAGUE_MARKET_COMMENTARY_TERMS = (
    "stocks are mixed",
    "markets mixed",
    "market commentary",
    "what to watch",
    "investors weigh",
    "wall street opens",
    "futures edge",
    "stocks drift",
    "market update"
)

REGIONAL_LOW_IMPACT_TERMS = (
    "county",
    "municipal",
    "local",
    "regional",
    "statewide"
)

MARKET_IMPACT_RULES = (
    {
        "category": "Fed Policy",
        "tier": "CRITICAL",
        "weight": 95,
        "required_any": ("Fed", "Federal Reserve", "FOMC", "Powell"),
        "context_any": (
            "rate cut",
            "rate cuts",
            "rate hike",
            "rate hikes",
            "interest rates",
            "policy rate",
            "dot plot",
            "press conference",
            "rates",
            "cuts rates",
            "hikes rates"
        ),
        "reason": "Federal Reserve policy directly reprices rates, equities, and risk assets."
    },
    {
        "category": "Inflation Shock",
        "tier": "CRITICAL",
        "weight": 92,
        "required_any": ("CPI", "PCE", "inflation"),
        "context_any": HIGH_IMPACT_MODIFIERS + (
            "core",
            "prices",
            "hot",
            "cool",
            "above forecast",
            "below forecast"
        ),
        "reason": "Inflation surprises change expected Fed policy and discount rates."
    },
    {
        "category": "Labor Market Shock",
        "tier": "HIGH",
        "weight": 88,
        "required_any": (
            "jobs report",
            "payrolls",
            "unemployment",
            "wage growth",
            "nonfarm payrolls"
        ),
        "context_any": HIGH_IMPACT_MODIFIERS + (
            "misses",
            "beats",
            "claims",
            "labor market",
            "jobs report",
            "payrolls",
            "unemployment",
            "wage growth",
            "nonfarm payrolls"
        ),
        "reason": "Labor-market shocks affect recession risk and rate expectations."
    },
    {
        "category": "Treasury and Liquidity Stress",
        "tier": "HIGH",
        "weight": 86,
        "required_any": (
            "Treasury yields",
            "bond market",
            "yield curve",
            "credit spreads",
            "liquidity"
        ),
        "context_any": HIGH_IMPACT_MODIFIERS + (
            "stress",
            "auction",
            "selloff",
            "spike",
            "inversion"
        ),
        "reason": "Bond-market and liquidity stress can drive cross-asset repricing."
    },
    {
        "category": "Recession Signal",
        "tier": "HIGH",
        "weight": 84,
        "required_any": ("recession", "GDP contraction", "contracts", "contraction"),
        "context_any": (
            "GDP",
            "economy",
            "warning",
            "signal",
            "slump",
            "downturn",
            "negative growth"
        ),
        "reason": "Recession signals change earnings expectations and risk appetite."
    },
    {
        "category": "Energy Supply Shock",
        "tier": "HIGH",
        "weight": 82,
        "required_any": ("oil", "crude", "energy", "Strait of Hormuz", "Iran"),
        "context_any": (
            "disruption",
            "supply",
            "attack",
            "conflict",
            "war",
            "sanctions",
            "Hormuz",
            "Iran",
            "Middle East",
            "shipping"
        ),
        "reason": "Energy supply disruptions can quickly affect inflation and margins."
    },
    {
        "category": "China Taiwan Escalation",
        "tier": "HIGH",
        "weight": 80,
        "required_any": ("China", "Taiwan"),
        "context_any": (
            "escalation",
            "military",
            "sanctions",
            "blockade",
            "invasion",
            "conflict",
            "tariffs",
            "export controls",
            "warning",
            "warns"
        ),
        "reason": "China/Taiwan escalation threatens global trade and semiconductor supply chains."
    },
    {
        "category": "Mega-Cap Earnings",
        "tier": "ELEVATED",
        "weight": 76,
        "required_any": EARNINGS_TERMS,
        "context_any": MEGA_CAP_TERMS + PORTFOLIO_TERMS,
        "reason": "Mega-cap or portfolio earnings can move indexes and portfolio holdings."
    },
    {
        "category": "Major Regulatory Action",
        "tier": "ELEVATED",
        "weight": 74,
        "required_any": ("SEC", "DOJ", "FTC", "antitrust", "regulatory"),
        "context_any": (
            "lawsuit",
            "investigation",
            "enforcement",
            "charges",
            "settlement",
            "rule",
            "probe",
            "sues"
        ),
        "reason": "Major regulatory action can alter sector economics or company risk."
    },
    {
        "category": "Portfolio Company Event",
        "tier": "ELEVATED",
        "weight": 68,
        "required_any": PORTFOLIO_TERMS,
        "context_any": HIGH_IMPACT_MODIFIERS + EARNINGS_TERMS + (
            "investigation",
            "lawsuit",
            "guidance",
            "acquisition",
            "merger"
        ),
        "reason": "Portfolio-linked company news has direct portfolio relevance."
    },
    {
        "category": "AI and Semiconductor Cycle",
        "tier": "MODERATE",
        "weight": 52,
        "required_any": AI_SEMICONDUCTOR_TERMS,
        "context_any": (
            "earnings",
            "guidance",
            "export controls",
            "demand",
            "supply",
            "data center",
            "chip"
        ),
        "reason": "AI and semiconductor developments can affect growth leadership."
    },
    {
        "category": "Generic Economic Data",
        "tier": "LOW",
        "weight": 22,
        "required_any": ("economic indicators", "GDP", "income", "spending", "statistics"),
        "context_any": ROUTINE_RELEASE_TERMS + ("latest", "numbers", "estimate"),
        "reason": "Routine economic data is monitored but lacks a clear market shock."
    },
    {
        "category": "Routine Government Release",
        "tier": "LOW",
        "weight": 12,
        "required_any": ROUTINE_RELEASE_TERMS,
        "context_any": ("government", "agency", "bureau", "department", "BEA", "BLS"),
        "reason": "Routine releases are lower priority without a market-moving surprise."
    },
    {
        "category": "Vague Market Commentary",
        "tier": "LOW",
        "weight": 10,
        "required_any": VAGUE_MARKET_COMMENTARY_TERMS,
        "context_any": ("stocks", "market", "investors", "wall street"),
        "reason": "General market commentary lacks a specific market-moving catalyst."
    },
    {
        "category": "Low-Impact Regional News",
        "tier": "LOW",
        "weight": 8,
        "required_any": REGIONAL_LOW_IMPACT_TERMS,
        "context_any": ("economy", "business", "jobs", "statistics", "market"),
        "reason": "Regional news is lower priority unless tied to broader market stress."
    }
)

NARRATIVE_CATEGORY_IMPORTANCE = {
    "Fed Policy": 8,
    "Inflation Shock": 8,
    "Labor Market Shock": 7,
    "Treasury and Liquidity Stress": 7,
    "Recession Signal": 7,
    "Energy Supply Shock": 6,
    "China Taiwan Escalation": 6,
    "Mega-Cap Earnings": 5,
    "Major Regulatory Action": 5,
    "Portfolio Company Event": 5,
    "AI and Semiconductor Cycle": 3,
    "Generic Economic Data": 1,
    "Routine Government Release": 0,
    "Vague Market Commentary": 0,
    "Low-Impact Regional News": 0,
    "No Clear Market Catalyst": 0
}

NARRATIVE_TITLE_BY_CATEGORY = {
    "Fed Policy": "Federal Reserve Policy Outlook",
    "Inflation Shock": "Inflation",
    "Labor Market Shock": "Labor Market",
    "Treasury and Liquidity Stress": "Treasury Market",
    "Recession Signal": "Recession Risk",
    "Energy Supply Shock": "Energy Market",
    "China Taiwan Escalation": "China/Taiwan",
    "Mega-Cap Earnings": "Mega-Cap Earnings",
    "Major Regulatory Action": "Regulatory Action",
    "Portfolio Company Event": "Portfolio-Relevant Events",
    "AI and Semiconductor Cycle": "AI and Semiconductor Cycle",
    "Generic Economic Data": "General Economic Data",
    "Routine Government Release": "Routine Government Releases",
    "Vague Market Commentary": "General Market Developments",
    "Low-Impact Regional News": "Regional Developments",
    "No Clear Market Catalyst": "General Market Developments"
}

NARRATIVE_STOPWORDS = {
    "about",
    "after",
    "ahead",
    "amid",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "could",
    "for",
    "from",
    "has",
    "have",
    "his",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "more",
    "new",
    "not",
    "of",
    "on",
    "or",
    "over",
    "says",
    "that",
    "the",
    "their",
    "to",
    "up",
    "what",
    "while",
    "with",
    "your"
}


def _local_name(tag):

    return str(tag).rsplit("}", 1)[-1].lower()


def _clean_text(value):

    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)

    return re.sub(r"\s+", " ", text).strip()


def _parse_published_date(value):

    value = str(value or "").strip()

    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        parsed = None

    if parsed is None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _first_child_text(element, names):

    expected_names = set(names)

    for child in element:
        if _local_name(child.tag) in expected_names:
            text = _clean_text(child.text)

            if text:
                return text

    return ""


def _entry_link(element):

    for child in element:
        if _local_name(child.tag) != "link":
            continue

        href = str(child.attrib.get("href") or "").strip()

        if href:
            return href

        text = _clean_text(child.text)

        if text:
            return text

    return ""


def _parse_feed(content, source):

    root = ET.fromstring(content)
    entries = [
        element
        for element in root.iter()
        if _local_name(element.tag) in {"item", "entry"}
    ]
    articles = []

    for entry in entries:
        title = _first_child_text(entry, {"title"})

        if not title:
            continue

        published_text = _first_child_text(
            entry,
            {"pubdate", "published", "updated", "date"}
        )
        summary = _first_child_text(
            entry,
            {"description", "summary", "content", "encoded"}
        )
        articles.append({
            "title": title,
            "source": source["name"],
            "published": _parse_published_date(published_text),
            "published_text": published_text,
            "link": _entry_link(entry),
            "summary": summary,
            "official_source": bool(source.get("official"))
        })

    return articles


def _fetch_source(source, timeout=8):

    request = urllib.request.Request(
        source["url"],
        headers={
            "User-Agent": (
                "Echo-News-Agent/1.0 "
                "(public RSS reader; contact: local-user)"
            ),
            "Accept": (
                "application/rss+xml, application/atom+xml, "
                "application/xml, text/xml"
            )
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read()

        articles = _parse_feed(content, source)

        return {
            "source": source["name"],
            "status": "OK",
            "articles": articles,
            "error": ""
        }
    except Exception as error:
        return {
            "source": source["name"],
            "status": "FAILED",
            "articles": [],
            "error": _clean_text(error)
        }


def _find_matches(text, terms):

    matches = []

    for term in terms:
        pattern = (
            r"(?<![A-Za-z0-9])"
            + re.escape(term)
            + r"(?![A-Za-z0-9])"
        )

        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(term)

    return matches


def _rule_matches(text, rule):

    required_matches = _find_matches(text, rule["required_any"])
    context_matches = _find_matches(text, rule["context_any"])

    return required_matches, context_matches


def _score_impact_categories(searchable_text):

    matches = []

    for rule in MARKET_IMPACT_RULES:
        required_matches, context_matches = _rule_matches(
            searchable_text,
            rule
        )

        if not required_matches or not context_matches:
            continue

        matches.append({
            "category": rule["category"],
            "impact_tier": rule["tier"],
            "weight": rule["weight"],
            "required_matches": required_matches,
            "context_matches": context_matches,
            "reason": rule["reason"]
        })

    if not matches:
        return [{
            "category": "No Clear Market Catalyst",
            "impact_tier": "LOW",
            "weight": 0,
            "required_matches": [],
            "context_matches": [],
            "reason": (
                "No high-impact market catalyst matched the headline "
                "or summary."
            )
        }]

    return sorted(
        matches,
        key=lambda match: (
            -match["weight"],
            -IMPACT_TIER_RANK[match["impact_tier"]],
            match["category"]
        )
    )


def _is_routine_low_impact_headline(title):

    title_text = str(title or "")

    if re.search(
        r"\bmajor economic indicators latest numbers\b",
        title_text,
        flags=re.IGNORECASE
    ):
        return True

    routine_matches = _find_matches(title_text, ROUTINE_RELEASE_TERMS)
    high_impact_matches = _find_matches(title_text, HIGH_IMPACT_MODIFIERS)

    return bool(routine_matches) and not high_impact_matches


def _score_article(article, current_date=None):

    current_date = current_date or datetime.now(timezone.utc).date()
    searchable_text = f"{article['title']} {article['summary']}"
    portfolio_matches = _find_matches(searchable_text, PORTFOLIO_TERMS)
    watchlist_matches = _find_matches(searchable_text, WATCHLIST_TERMS)
    macro_matches = _find_matches(searchable_text, MACRO_TERMS)
    market_matches = _find_matches(searchable_text, MARKET_TERMS)
    world_matches = _find_matches(searchable_text, WORLD_EVENT_TERMS)
    urgency_matches = _find_matches(searchable_text, URGENCY_TERMS)
    healthcare_matches = _find_matches(searchable_text, HEALTHCARE_TERMS)
    ai_matches = _find_matches(searchable_text, AI_SEMICONDUCTOR_TERMS)
    energy_matches = _find_matches(searchable_text, ENERGY_TERMS)
    crypto_matches = _find_matches(searchable_text, CRYPTO_TERMS)
    regulatory_matches = _find_matches(searchable_text, REGULATORY_TERMS)
    earnings_matches = _find_matches(searchable_text, EARNINGS_TERMS)
    rates_matches = _find_matches(searchable_text, RATES_TERMS)
    central_bank_matches = _find_matches(
        searchable_text,
        ("Fed", "Federal Reserve", "FOMC", "Powell")
    )
    impact_matches = _score_impact_categories(searchable_text)
    top_impact = impact_matches[0]
    routine_low_impact_headline = _is_routine_low_impact_headline(
        article["title"]
    )

    if routine_low_impact_headline:
        top_impact = {
            "category": "Generic Economic Data",
            "impact_tier": "LOW",
            "weight": 22,
            "required_matches": _find_matches(
                searchable_text,
                ("economic indicators", "GDP", "income", "spending")
            ),
            "context_matches": _find_matches(
                searchable_text,
                ROUTINE_RELEASE_TERMS + ("latest", "numbers")
            ),
            "reason": (
                "Routine indicator headline is capped below "
                "market-moving catalysts."
            )
        }
        impact_matches = [top_impact] + [
            match for match in impact_matches
            if match["category"] != top_impact["category"]
        ]
    portfolio_score = top_impact["weight"] if portfolio_matches else 0
    watchlist_score = min(top_impact["weight"], 55) if watchlist_matches else 0
    macro_score = top_impact["weight"] if macro_matches else 0
    market_score = (
        top_impact["weight"]
        if market_matches or top_impact["weight"] >= 50
        else 0
    )
    world_event_score = top_impact["weight"] if world_matches else 0
    urgency_score = min(8, len(urgency_matches) * 2)
    official_bonus = 3 if article["official_source"] else 0
    today_bonus = (
        2
        if article["published"]
        and article["published"].date() == current_date
        else 0
    )
    relevance_bonus = 0

    if portfolio_matches or watchlist_matches:
        relevance_bonus += 5

    if urgency_matches and top_impact["weight"] >= 50:
        relevance_bonus += urgency_score

    if article["official_source"] and top_impact["weight"] >= 70:
        relevance_bonus += official_bonus

    if today_bonus and top_impact["weight"] >= 22:
        relevance_bonus += today_bonus

    total_score = min(100, top_impact["weight"] + relevance_bonus)
    tags = []

    for tag, matches in (
        ("PORTFOLIO", portfolio_matches),
        ("WATCHLIST", watchlist_matches),
        ("MACRO", macro_matches),
        ("MARKET", market_matches),
        ("WORLD_EVENT", world_matches),
        ("REGULATORY", regulatory_matches),
        ("EARNINGS", earnings_matches),
        ("CENTRAL_BANK", central_bank_matches),
        ("ENERGY", energy_matches),
        ("AI_SEMICONDUCTOR", ai_matches),
        ("HEALTHCARE", healthcare_matches),
        ("CRYPTO", crypto_matches),
        ("RATES", rates_matches)
    ):
        if matches:
            tags.append(tag)

    if not tags:
        tags = ["UNKNOWN"]

    if total_score >= 70:
        relevance = "HIGH"
    elif total_score >= 35:
        relevance = "MEDIUM"
    else:
        relevance = "LOW"

    all_matches = []

    for matches in (
        portfolio_matches,
        watchlist_matches,
        macro_matches,
        market_matches,
        world_matches,
        urgency_matches,
        regulatory_matches,
        earnings_matches,
        healthcare_matches,
        ai_matches,
        energy_matches,
        crypto_matches,
        rates_matches
    ):
        for term in matches:
            if term not in all_matches:
                all_matches.append(term)

    article.update({
        "matched_terms": all_matches,
        "portfolio_matches": portfolio_matches,
        "watchlist_matches": watchlist_matches,
        "macro_matches": macro_matches,
        "market_matches": market_matches,
        "world_event_matches": world_matches,
        "urgency_matches": urgency_matches,
        "impact_matches": impact_matches,
        "impact_category": top_impact["category"],
        "impact_tier": top_impact["impact_tier"],
        "ranking_reason": top_impact["reason"],
        "category_tags": sorted(
            tags,
            key=lambda tag: TAG_ORDER.index(tag)
        ),
        "portfolio_score": portfolio_score,
        "watchlist_score": watchlist_score,
        "macro_score": macro_score,
        "market_score": market_score,
        "world_event_score": world_event_score,
        "urgency_score": urgency_score,
        "official_source_bonus": official_bonus,
        "today_bonus": today_bonus,
        "total_score": total_score,
        "relevance_score": total_score,
        "relevance": relevance
    })

    return article


def _article_sort_key(article):

    published = article["published"]
    published_timestamp = (
        published.timestamp()
        if published is not None
        else float("-inf")
    )

    return (
        -article["total_score"],
        -IMPACT_TIER_RANK[article["impact_tier"]],
        -published_timestamp,
        article["title"].casefold(),
        article["source"].casefold()
    )


def _deduplicate_articles(articles):

    unique_articles = {}

    for article in articles:
        title_key = re.sub(
            r"\s+",
            " ",
            article["title"]
        ).strip().casefold()
        existing = unique_articles.get(title_key)

        if existing is None or _article_sort_key(article) < (
            _article_sort_key(existing)
        ):
            unique_articles[title_key] = article

    return sorted(unique_articles.values(), key=_article_sort_key)


def _narrative_topic_tokens(article):

    text = f"{article['title']} {article['summary']}"
    tokens = []

    for token in re.findall(r"[A-Za-z][A-Za-z0-9']+", text.casefold()):
        token = token.strip("'")

        if len(token) < 4 or token in NARRATIVE_STOPWORDS:
            continue

        if token.endswith("'s"):
            token = token[:-2]

        if token not in tokens:
            tokens.append(token)

    return tokens


def _narrative_entities(article):

    entities = []

    for term in (
        article["matched_terms"]
        + article["portfolio_matches"]
        + article["watchlist_matches"]
    ):
        normalized = str(term).strip()

        if normalized and normalized not in entities:
            entities.append(normalized)

    return entities


def _narrative_topic_bucket(article):

    text = f"{article['title']} {article['summary']}"

    for bucket, terms in (
        ("federal-reserve", ("Fed", "Federal Reserve", "FOMC", "Powell", "Warsh")),
        ("inflation", ("CPI", "PCE", "inflation", "prices")),
        ("labor-market", ("jobs", "payrolls", "unemployment", "wage growth")),
        ("treasury-market", ("Treasury", "yield", "bond market", "liquidity")),
        ("middle-east-energy", ("Iran", "Hormuz", "Middle East", "oil", "crude")),
        ("china-taiwan", ("China", "Taiwan")),
        ("regulatory", ("SEC", "DOJ", "FTC", "antitrust", "lawsuit")),
        ("mega-cap-earnings", MEGA_CAP_TERMS + EARNINGS_TERMS),
        ("portfolio", PORTFOLIO_TERMS)
    ):
        if _find_matches(text, terms):
            return bucket

    tokens = _narrative_topic_tokens(article)

    return "-".join(tokens[:2]) if tokens else "general"


def _narrative_title(category, topic_bucket):

    if topic_bucket == "middle-east-energy":
        return "Middle East Energy Risk"

    if topic_bucket == "federal-reserve":
        return "Federal Reserve Policy Outlook"

    if topic_bucket == "china-taiwan":
        return "China/Taiwan Escalation"

    return NARRATIVE_TITLE_BY_CATEGORY.get(
        category,
        category or "General Market Developments"
    )


def _narrative_key(article):

    category = article["impact_category"]
    topic_bucket = _narrative_topic_bucket(article)

    if category == "Energy Supply Shock":
        return category, "middle-east-energy"

    high_level_categories = {
        "Fed Policy",
        "Inflation Shock",
        "Labor Market Shock",
        "Treasury and Liquidity Stress",
        "Recession Signal",
        "Energy Supply Shock",
        "China Taiwan Escalation",
        "Major Regulatory Action",
        "Mega-Cap Earnings",
        "Portfolio Company Event"
    }

    if category in high_level_categories:
        return category, topic_bucket

    tags = "-".join(article["category_tags"][:2])
    tokens = _narrative_topic_tokens(article)

    return category, tags, "-".join(tokens[:2])


def _narrative_reason(narrative):

    count = narrative["supporting_article_count"]
    category = narrative["impact_category"]
    representative = narrative["representative_article"]

    if category == "Fed Policy":
        return (
            f"{count} related Fed-policy stories point to rates as the "
            "dominant market narrative."
        )

    if narrative["topic_bucket"] == "middle-east-energy":
        return (
            f"{count} related Iran, Hormuz, or oil headlines indicate an "
            "energy-linked geopolitical market narrative."
        )

    if count > 1:
        return (
            f"{count} related stories share impact category {category} "
            f"and common market tags."
        )

    return representative["ranking_reason"]


def _narrative_importance_tier(score):

    if score >= 95:
        return "CRITICAL"

    if score >= 80:
        return "HIGH"

    if score >= 60:
        return "ELEVATED"

    if score >= 35:
        return "MODERATE"

    return "LOW"


def _narrative_sort_key(narrative):

    return (
        -narrative["narrative_score"],
        -IMPACT_TIER_RANK.get(narrative["narrative_importance_tier"], 0),
        -narrative["supporting_article_count"],
        narrative["narrative_title"].casefold()
    )


def build_news_narratives(articles):

    grouped_articles = {}

    for article in articles:
        grouped_articles.setdefault(_narrative_key(article), []).append(article)

    narratives = []

    for key, grouped in grouped_articles.items():
        grouped = sorted(grouped, key=_article_sort_key)
        representative = grouped[0]
        category = representative["impact_category"]
        topic_bucket = (
            key[1]
            if len(key) > 1
            else _narrative_topic_bucket(representative)
        )
        article_count = len(grouped)
        count_bonus = min(10, max(0, article_count - 1) * 3)
        category_bonus = NARRATIVE_CATEGORY_IMPORTANCE.get(category, 0)
        narrative_score = min(
            100,
            representative["total_score"] + count_bonus + category_bonus
        )
        narrative = {
            "narrative_title": _narrative_title(category, topic_bucket),
            "narrative_score": narrative_score,
            "narrative_importance_tier": (
                _narrative_importance_tier(narrative_score)
            ),
            "supporting_article_count": article_count,
            "representative_headline": representative["title"],
            "representative_article": representative,
            "impact_category": category,
            "topic_bucket": topic_bucket,
            "category_tags": sorted(
                {
                    tag
                    for article in grouped
                    for tag in article["category_tags"]
                },
                key=lambda tag: TAG_ORDER.index(tag)
            ),
            "supporting_articles": grouped,
            "topic_tokens": sorted(
                {
                    token
                    for article in grouped
                    for token in _narrative_topic_tokens(article)
                }
            ),
            "entities": sorted(
                {
                    entity
                    for article in grouped
                    for entity in _narrative_entities(article)
                },
                key=str.casefold
            )
        }
        narrative["narrative_reason"] = _narrative_reason(narrative)
        narratives.append(narrative)

    return sorted(narratives, key=_narrative_sort_key)


def collect_news(sources=None, fetcher=None, current_date=None):

    sources = tuple(
        DEFAULT_NEWS_SOURCES
        if sources is None
        else sources
    )
    fetcher = fetcher or _fetch_source

    if not sources:
        return {
            "status": "OFFLINE",
            "source_health": [],
            "articles": [],
            "narratives": [],
            "failed_source_count": 0,
            "successful_source_count": 0
        }

    source_results = []

    with ThreadPoolExecutor(max_workers=min(6, len(sources))) as executor:
        futures = {
            executor.submit(fetcher, source): source
            for source in sources
        }

        for future in as_completed(futures):
            source = futures[future]

            try:
                result = future.result()
            except Exception as error:
                result = {
                    "source": source["name"],
                    "status": "FAILED",
                    "articles": [],
                    "error": _clean_text(error)
                }

            source_results.append(result)

    source_order = {
        source["name"]: index
        for index, source in enumerate(sources)
    }
    source_results.sort(
        key=lambda result: source_order.get(result["source"], 999)
    )
    articles = []

    for result in source_results:
        for article in result["articles"]:
            articles.append(_score_article(article, current_date=current_date))

    articles = _deduplicate_articles(articles)
    narratives = build_news_narratives(articles)
    successful_source_count = sum(
        result["status"] == "OK"
        for result in source_results
    )
    failed_source_count = sum(
        result["status"] == "FAILED"
        for result in source_results
    )

    if successful_source_count == 0 or not articles:
        status = "OFFLINE"
    elif failed_source_count > 0 or len(articles) < 5:
        status = "DEGRADED"
    else:
        status = "ACTIVE"

    return {
        "status": status,
        "source_health": [
            {
                "source": result["source"],
                "status": result["status"],
                "article_count": len(result["articles"]),
                "error": result["error"]
            }
            for result in source_results
        ],
        "articles": articles,
        "narratives": narratives,
        "failed_source_count": failed_source_count,
        "successful_source_count": successful_source_count
    }


def _top_story(articles, score_field):

    matching_articles = [
        article
        for article in articles
        if article[score_field] > 0
    ]

    return matching_articles[0]["title"] if matching_articles else "None"


def _top_ranked_story(articles):

    return articles[0]["title"] if articles else "None"


def _top_ranked_narrative(narratives):

    return narratives[0]["narrative_title"] if narratives else "None"


def _format_story_list(articles, match_field):

    lines = []

    for article in articles[:10]:
        matched_terms = ", ".join(article[match_field]) or "None"
        link = article["link"] or "N/A"
        lines.append(
            f"{article['title']} | Source {article['source']} | "
            f"Score {article['total_score']} | "
            f"Impact Category {article['impact_category']} | "
            f"Impact Tier {article['impact_tier']} | "
            f"Reason {article['ranking_reason']} | "
            f"Matched Terms {matched_terms} | Link {link}"
        )

    return lines or ["None"]


def build_news_report(news_data):

    articles = news_data["articles"]
    narratives = news_data.get("narratives") or []
    top_narrative = narratives[0] if narratives else None
    portfolio_articles = [
        article for article in articles if article["portfolio_score"] > 0
    ]
    watchlist_articles = [
        article for article in articles if article["watchlist_score"] > 0
    ]
    macro_articles = [
        article for article in articles if article["macro_score"] > 0
    ]
    market_articles = [
        article for article in articles if article["market_score"] > 0
    ]
    world_articles = [
        article for article in articles if article["world_event_score"] > 0
    ]
    executive_brief = [
        f"News Agent Status: {news_data['status']}",
        (
            f"Top Market Narrative: "
            f"{_top_ranked_narrative(narratives)}"
        ),
        (
            f"Supporting Articles: "
            f"{top_narrative['supporting_article_count'] if top_narrative else 0}"
        ),
        (
            f"Top Narrative Score: "
            f"{top_narrative['narrative_score'] if top_narrative else 0}"
        ),
        (
            f"Representative Headline: "
            f"{top_narrative['representative_headline'] if top_narrative else 'None'}"
        ),
        (
            f"Top Narrative Reason: "
            f"{top_narrative['narrative_reason'] if top_narrative else 'None'}"
        ),
        (
            f"Top Portfolio Story: "
            f"{_top_story(portfolio_articles, 'portfolio_score')}"
        ),
        (
            f"Top Watchlist Story: "
            f"{_top_story(watchlist_articles, 'watchlist_score')}"
        ),
        f"Top Macro Story: {_top_story(macro_articles, 'macro_score')}",
        (
            f"Top World Event Story: "
            f"{_top_story(world_articles, 'world_event_score')}"
        ),
        (
            f"High Relevance Stories: "
            f"{sum(article['relevance'] == 'HIGH' for article in articles)}"
        ),
        f"Portfolio-Relevant Stories: {len(portfolio_articles)}",
        f"Watchlist-Relevant Stories: {len(watchlist_articles)}",
        f"Macro-Relevant Stories: {len(macro_articles)}",
        f"World Event Stories: {len(world_articles)}",
        f"Failed Sources: {news_data['failed_source_count']}",
        "",
        (
            "News Agent is observational only and does not generate "
            "investment recommendations."
        )
    ]
    full_report = ["Source Health:"]

    if news_data["source_health"]:
        for source in news_data["source_health"]:
            error = source["error"] or "None"
            full_report.append(
                f"{source['source']} | Status {source['status']} | "
                f"Articles {source['article_count']} | Error {error}"
            )
    else:
        full_report.append("No news sources connected.")

    if not articles:
        if news_data["source_health"]:
            full_report.append("")
            full_report.append(
                "No news sources connected."
                if news_data["successful_source_count"] == 0
                else "No news articles available."
            )

        return {
            "executive_brief": executive_brief,
            "full_report": full_report,
            "data": news_data
        }

    full_report.extend(["", "Top Ranked Narratives:"])

    for rank, narrative in enumerate(narratives[:10], start=1):
        full_report.extend([
            f"{rank}. {narrative['narrative_title']}",
            f"   Narrative Score: {narrative['narrative_score']}",
            f"   Tier: {narrative['narrative_importance_tier']}",
            (
                "   Supporting Articles: "
                f"{narrative['supporting_article_count']}"
            ),
            f"   Representative Headline: {narrative['representative_headline']}",
            f"   Narrative Reason: {narrative['narrative_reason']}",
            "   Supporting Headlines:"
        ])

        for article in narrative["supporting_articles"][:8]:
            full_report.append(f"   - {article['title']}")

    full_report.extend(["", "Top Ranked Stories:"])

    for rank, article in enumerate(articles[:10], start=1):
        tags = ", ".join(article["category_tags"])
        full_report.append(
            f"{rank}. {article['title']} | Source {article['source']} | "
            f"Relevance Score {article['total_score']} | "
            f"Impact Category {article['impact_category']} | "
            f"Impact Tier {article['impact_tier']} | "
            f"Relevance {article['relevance']} | "
            f"Reason {article['ranking_reason']} | Tags {tags}"
        )

    for heading, story_articles, match_field in (
        (
            "Portfolio-Relevant Stories:",
            portfolio_articles,
            "portfolio_matches"
        ),
        (
            "Watchlist-Relevant Stories:",
            watchlist_articles,
            "watchlist_matches"
        ),
        ("Macro-Relevant Stories:", macro_articles, "macro_matches"),
        (
            "World Event Stories:",
            world_articles,
            "world_event_matches"
        )
    ):
        full_report.extend([
            "",
            heading,
            *_format_story_list(story_articles, match_field)
        ])

    return {
        "executive_brief": executive_brief,
        "full_report": full_report,
        "data": news_data
    }


def get_news_report(sources=None, fetcher=None, current_date=None):

    return build_news_report(
        collect_news(
            sources=sources,
            fetcher=fetcher,
            current_date=current_date
        )
    )


def get_news():

    report = get_news_report()

    return (
        ["NEWS AGENT EXECUTIVE BRIEF", ""]
        + report["executive_brief"]
        + ["", "NEWS AGENT FULL REPORT", ""]
        + report["full_report"]
    )
