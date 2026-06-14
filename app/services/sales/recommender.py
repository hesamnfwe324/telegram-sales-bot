from app.core.logging import get_logger

logger = get_logger(__name__)

PLANS = {
    "vps": [
        {"name": "VPS Starter", "price": 5, "cpu": 1, "ram": 1, "disk": 25, "bandwidth": "1TB", "best_for": ["personal", "testing", "small blog", "dev environment"]},
        {"name": "VPS Basic", "price": 10, "cpu": 2, "ram": 2, "disk": 50, "bandwidth": "2TB", "best_for": ["wordpress", "small website", "small api"]},
        {"name": "VPS Standard", "price": 20, "cpu": 4, "ram": 4, "disk": 80, "bandwidth": "4TB", "best_for": ["ecommerce", "medium traffic", "nodejs app", "django", "laravel"]},
        {"name": "VPS Advanced", "price": 40, "cpu": 8, "ram": 8, "disk": 160, "bandwidth": "8TB", "best_for": ["high traffic", "multiple apps", "game server small", "saas"]},
        {"name": "VPS Pro", "price": 80, "cpu": 16, "ram": 16, "disk": 320, "bandwidth": "Unlimited", "best_for": ["enterprise", "high load", "game server", "streaming"]},
    ],
    "cloud": [
        {"name": "Cloud Starter", "price": 15, "cpu": 2, "ram": 4, "disk": 50, "bandwidth": "5TB", "best_for": ["startups", "auto-scaling apps", "microservices small"]},
        {"name": "Cloud Business", "price": 50, "cpu": 8, "ram": 16, "disk": 200, "bandwidth": "10TB", "best_for": ["growing business", "high availability", "ecommerce enterprise", "saas platform"]},
        {"name": "Cloud Enterprise", "price": 150, "cpu": 32, "ram": 64, "disk": 500, "bandwidth": "Unlimited", "best_for": ["large scale", "enterprise apps", "big data", "kubernetes"]},
    ],
    "dedicated": [
        {"name": "Dedicated Entry", "price": 80, "cpu": "Intel Xeon E3 4-core", "ram": 32, "disk": "2×1TB HDD", "bandwidth": "Unlimited", "best_for": ["database server", "game server", "bare metal performance"]},
        {"name": "Dedicated Business", "price": 150, "cpu": "Intel Xeon E5 8-core", "ram": 64, "disk": "2×2TB SSD", "bandwidth": "Unlimited", "best_for": ["high performance web", "video streaming", "fintech", "large database"]},
        {"name": "Dedicated Enterprise", "price": 300, "cpu": "Dual Intel Xeon 16-core", "ram": 128, "disk": "4×1TB NVMe", "bandwidth": "Unlimited", "best_for": ["machine learning", "big data analytics", "enterprise ERP", "massive scale"]},
    ],
}

USE_CASE_SERVICE_MAP = {
    "wordpress": "vps",
    "blog": "vps",
    "personal": "vps",
    "testing": "vps",
    "dev": "vps",
    "ecommerce": "cloud",
    "saas": "cloud",
    "startup": "cloud",
    "microservices": "cloud",
    "kubernetes": "cloud",
    "machine learning": "dedicated",
    "ml": "dedicated",
    "game server": "dedicated",
    "database": "dedicated",
    "streaming": "dedicated",
    "fintech": "dedicated",
}

COMPARISON_LANGS = {
    "en": {
        "header": "📦 *Recommended Plans for You*",
        "footer": "💬 Want more details or a custom quote? Just ask!",
        "month": "month",
        "cpu": "CPU",
        "ram": "RAM",
        "disk": "Storage",
        "bw": "Bandwidth",
        "best": "Best for",
    },
    "fa": {
        "header": "📦 *پلن‌های پیشنهادی برای شما*",
        "footer": "💬 برای اطلاعات بیشتر یا قیمت سفارشی بپرسید!",
        "month": "ماه",
        "cpu": "پردازنده",
        "ram": "RAM",
        "disk": "فضا",
        "bw": "پهنای باند",
        "best": "مناسب برای",
    },
    "ar": {
        "header": "📦 *الخطط الموصى بها لك*",
        "footer": "💬 هل تريد المزيد من التفاصيل أو عرض مخصص؟ فقط اسأل!",
        "month": "شهر",
        "cpu": "المعالج",
        "ram": "الذاكرة",
        "disk": "التخزين",
        "bw": "النطاق الترددي",
        "best": "الأفضل لـ",
    },
    "tr": {
        "header": "📦 *Sizin İçin Önerilen Planlar*",
        "footer": "💬 Daha fazla bilgi veya özel teklif için sorun!",
        "month": "ay",
        "cpu": "İşlemci",
        "ram": "RAM",
        "disk": "Depolama",
        "bw": "Bant Genişliği",
        "best": "En iyi kullanım",
    },
    "ru": {
        "header": "📦 *Рекомендованные планы для вас*",
        "footer": "💬 Нужны подробности или индивидуальное предложение? Просто спросите!",
        "month": "мес",
        "cpu": "ЦПУ",
        "ram": "RAM",
        "disk": "Диск",
        "bw": "Трафик",
        "best": "Лучше всего для",
    },
}


def recommend_plans(
    service_type: str,
    budget_max: float = None,
    requirements: dict = None,
) -> list[dict]:
    requirements = requirements or {}
    use_case = (requirements.get("use_case") or "").lower()

    if use_case and service_type in ("general", "none"):
        for keyword, svc in USE_CASE_SERVICE_MAP.items():
            if keyword in use_case:
                service_type = svc
                break

    plans = PLANS.get(service_type, [])
    if not plans:
        plans = PLANS["vps"]

    if budget_max:
        affordable = [p for p in plans if isinstance(p.get("price"), (int, float)) and p["price"] <= budget_max]
        if affordable:
            plans = affordable

    if use_case:
        def use_case_score(plan):
            best_for = plan.get("best_for", [])
            return sum(1 for kw in best_for if kw in use_case or use_case in kw)
        plans_with_scores = sorted(plans, key=use_case_score, reverse=True)
        if plans_with_scores:
            plans = plans_with_scores

    tech_level = requirements.get("tech_level", "unknown")
    if tech_level == "beginner" and len(plans) > 1:
        plans = plans[:2]
    elif tech_level == "expert":
        plans = plans[-3:]

    return plans[:3]


def format_plan_recommendation(plans: list[dict], language: str = "en") -> str:
    if not plans:
        return ""

    lang_data = COMPARISON_LANGS.get(language, COMPARISON_LANGS["en"])

    lines = [lang_data["header"], ""]
    for i, plan in enumerate(plans, 1):
        price = plan.get("price", "N/A")
        price_str = f"${price}/{lang_data['month']}" if isinstance(price, (int, float)) else str(price)
        lines.append(f"**{i}. {plan['name']}** — {price_str}")
        lines.append(f"   ├ {lang_data['cpu']}: {plan.get('cpu', 'N/A')}")
        lines.append(f"   ├ {lang_data['ram']}: {plan.get('ram', 'N/A')} GB")
        disk_val = plan.get('disk', 'N/A')
        disk_str = f"{disk_val} GB" if isinstance(disk_val, (int, float)) else str(disk_val)
        lines.append(f"   ├ {lang_data['disk']}: {disk_str}")
        lines.append(f"   └ {lang_data['bw']}: {plan.get('bandwidth', 'N/A')}")
        best_for = plan.get("best_for", [])
        if best_for:
            lines.append(f"   ✦ {lang_data['best']}: {', '.join(best_for[:3])}")
        lines.append("")

    lines.append(lang_data["footer"])
    return "\n".join(lines)


def get_all_plans_summary() -> dict:
    return {svc: [{"name": p["name"], "price": p["price"]} for p in plans] for svc, plans in PLANS.items()}
