from __future__ import annotations

import random
from copy import deepcopy


USE_CASES = {
    "": {"label": "Free choice", "label_zh": "自由选择", "hint": ""},
    "profile_avatar": {
        "label": "Profile / avatar",
        "label_zh": "个人资料 / 头像",
        "hint": "avatar composition, clear subject, suitable for social profile cropping",
    },
    "social_media_post": {
        "label": "Social media post",
        "label_zh": "社交媒体帖子",
        "hint": "feed-friendly composition, clear focal point, space for a short headline or caption",
    },
    "infographic_edu_visual": {
        "label": "Infographic / education visual",
        "label_zh": "信息图 / 教育视觉图",
        "hint": "clear structure, modular information, readable labels and icon-like visual hierarchy",
    },
    "youtube_thumbnail": {
        "label": "YouTube thumbnail",
        "label_zh": "YouTube 缩略图",
        "hint": "strong contrast, large subject, obvious title zone, high click appeal",
    },
    "comic_storyboard": {
        "label": "Comic / storyboard",
        "label_zh": "漫画 / 故事板",
        "hint": "sequential storytelling, clear action, consistent characters",
    },
    "product_marketing": {
        "label": "Product marketing",
        "label_zh": "产品营销",
        "hint": "emphasize selling points, material, use scenario, and brand feeling",
    },
    "ecommerce_main_image": {
        "label": "E-commerce main image",
        "label_zh": "电商主图",
        "hint": "clean commercial product composition, centered subject, clear silhouette, non-distracting background",
    },
    "game_asset": {
        "label": "Game asset",
        "label_zh": "游戏素材",
        "hint": "recognizable silhouette and form, suitable for concept art, game asset, or UI use",
    },
    "poster_flyer": {
        "label": "Poster / flyer",
        "label_zh": "海报 / 传单",
        "hint": "strong key visual, clear hierarchy, readable space for event or campaign text",
    },
    "app_web_design": {
        "label": "App / web design",
        "label_zh": "App / 网页设计",
        "hint": "high-fidelity interface layout, clear component hierarchy, realistic product screenshot feel",
    },
}


STYLES = {
    "": {"label": "Free style", "label_zh": "自由风格", "hint": ""},
    "photography": {"label": "Photography", "label_zh": "摄影", "hint": "real lens language, natural light, credible material and depth of field"},
    "cinematic_film_still": {"label": "Cinematic film still", "label_zh": "电影 / 剧照", "hint": "cinematic lighting, depth, color grade, and narrative mood"},
    "anime_manga": {"label": "Anime / manga", "label_zh": "动漫 / 漫画", "hint": "animation framing, clean linework, expressive character pose"},
    "illustration": {"label": "Illustration", "label_zh": "插画", "hint": "commercial illustration quality, complete image, unified style"},
    "sketch_line_art": {"label": "Sketch / line art", "label_zh": "草图 / 线稿", "hint": "clear linework and accurate structure for further design iteration"},
    "comic_graphic_novel": {"label": "Comic / graphic novel", "label_zh": "漫画 / 图像小说", "hint": "dramatic composition, ink lines, halftone, or panel-like visual treatment"},
    "3d_render": {"label": "3D render", "label_zh": "3D 渲染", "hint": "refined modeling, realistic materials, studio lighting, crisp edges"},
    "chibi_q_style": {"label": "Chibi / cute style", "label_zh": "Q版 / 萌系", "hint": "exaggerated proportions, cute silhouette, soft expression"},
    "isometric": {"label": "Isometric", "label_zh": "等距视角", "hint": "isometric composition and clear spatial relationships"},
    "pixel_art": {"label": "Pixel art", "label_zh": "像素艺术", "hint": "crisp pixel blocks, limited palette, retro game texture"},
    "oil_painting": {"label": "Oil painting", "label_zh": "油画", "hint": "thick brushwork, rich light and shadow, traditional painted texture"},
    "watercolor": {"label": "Watercolor", "label_zh": "水彩", "hint": "transparent washes, paper texture, soft edges"},
    "ink_chinese_style": {"label": "Ink / Chinese style", "label_zh": "水墨 / 中国风", "hint": "ink wash negative space, layered brushwork, eastern composition"},
    "retro_vintage": {"label": "Retro / vintage", "label_zh": "复古 / 怀旧", "hint": "vintage palette, grain texture, period-inspired layout"},
    "cyberpunk_sci_fi": {"label": "Cyberpunk / sci-fi", "label_zh": "赛博朋克 / 科幻", "hint": "neon light, future city, technology components, strong contrast"},
    "minimalism": {"label": "Minimalism", "label_zh": "极简主义", "hint": "few elements, generous whitespace, restrained color, clean hierarchy"},
}


SUBJECTS = {
    "": {"label": "Free subject", "label_zh": "自由主体", "hint": ""},
    "portrait_selfie": {"label": "Portrait / selfie", "label_zh": "人像 / 自拍", "hint": "clear face, natural pose, background supports the subject"},
    "influencer_model": {"label": "Influencer / model", "label_zh": "网红 / 模特", "hint": "fashion-forward presentation, commercial pose, social media feel"},
    "character": {"label": "Character", "label_zh": "角色", "hint": "clear character design, consistent costume, silhouette, and personality"},
    "group_couple": {"label": "Group / couple", "label_zh": "团体 / 情侣", "hint": "clear relationship between people, interactive gaze and pose"},
    "product": {"label": "Product", "label_zh": "产品", "hint": "clear material, structure, proportion, and selling points"},
    "food_drink": {"label": "Food / drink", "label_zh": "食品 / 饮料", "hint": "fresh appetizing texture and clean plating"},
    "fashion_item": {"label": "Fashion item", "label_zh": "时尚单品", "hint": "fabric, cut, accessory, and detail clarity"},
    "animal_creature": {"label": "Animal / creature", "label_zh": "动物 / 生物", "hint": "believable anatomy, natural motion, clear fur or skin texture"},
    "vehicle": {"label": "Vehicle", "label_zh": "车辆", "hint": "accurate exterior proportions, reflective materials, mechanical detail"},
    "architecture_interior": {"label": "Architecture / interior", "label_zh": "建筑 / 室内", "hint": "accurate perspective, light, material, and scale"},
    "landscape_nature": {"label": "Landscape / nature", "label_zh": "风景 / 自然", "hint": "environment depth, weather, light, foreground and background relationship"},
    "cityscape_street": {"label": "Cityscape / street", "label_zh": "城市风光 / 街道", "hint": "rich street details and clear city atmosphere"},
    "diagram_chart": {"label": "Diagram / chart", "label_zh": "图表", "hint": "accurate information structure, clear labels, readable layout"},
    "text_typography": {"label": "Text / typography", "label_zh": "文字 / 排版", "hint": "accurate readable text and natural typographic hierarchy"},
    "abstract_background": {"label": "Abstract / background", "label_zh": "抽象 / 背景", "hint": "texture, color, and depth suitable for background use"},
}


MODES = {"free": "Free", "light": "Light enhancement", "structured": "Structured template"}


def list_skill_options() -> dict:
    return {
        "use_cases": deepcopy(USE_CASES),
        "styles": deepcopy(STYLES),
        "subjects": deepcopy(SUBJECTS),
        "modes": dict(MODES),
    }


def _pick(group: dict, key: str) -> dict:
    return group.get(key or "", group[""])


def _selected_lines(use_case: str, style: str, subject: str) -> list[str]:
    items = [
        ("Use case", _pick(USE_CASES, use_case)),
        ("Style", _pick(STYLES, style)),
        ("Subject", _pick(SUBJECTS, subject)),
    ]
    return [f"{name}: {item['label']}. {item['hint']}" for name, item in items if item.get("hint")]


def build_skill_prompt(
    user_prompt: str,
    *,
    use_case: str = "",
    style: str = "",
    subject: str = "",
    mode: str = "free",
) -> str:
    base = (user_prompt or "").strip()
    if mode not in MODES:
        mode = "free"
    if mode == "free":
        return base
    lines = _selected_lines(use_case, style, subject)
    if not lines:
        return base
    if mode == "light":
        parts = [base] if base else ["Create a complete finished image."]
        parts.append("Enhance the prompt using these GPT Image 2 skill directions:")
        parts.extend(lines)
        parts.append("Keep the composition complete, the subject clear, and the details useful. Avoid unrelated elements.")
        return "\n".join(parts)

    goal = base or "Create a high-quality finished image based on the selected type."
    return "\n".join(
        [
            f"User goal: {goal}",
            "Generate the image using a structured GPT Image 2 prompt:",
            *lines,
            "Composition requirements: complete composition, clear visual hierarchy, strong material, light, space, and detail control.",
            "Readable text: if text appears in the image, it must be accurate, clear, and naturally typeset; avoid unnecessary text.",
            "Delivery target: the result should feel like a production-ready commercial visual, not a rough draft.",
        ]
    )


def random_skill_selection(seed: int | None = None) -> dict:
    rng = random.Random(seed)
    use_cases = [key for key in USE_CASES if key]
    styles = [key for key in STYLES if key]
    subjects = [key for key in SUBJECTS if key]
    return {
        "use_case": rng.choice(use_cases),
        "style": rng.choice(styles),
        "subject": rng.choice(subjects),
        "mode": rng.choice(["light", "structured"]),
    }
