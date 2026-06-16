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
            f"Top Market Story: "
            f"{_top_ranked_story(articles)}"
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
