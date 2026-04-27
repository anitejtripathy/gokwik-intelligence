from collections import defaultdict


class EngagementAgent:
    def run(self, content_items: list[dict], content_themes: dict) -> dict:
        print(f"[EngagementAgent] Computing stats for {len(content_items)} items")
        theme_map = {item.get("id", ""): item.get("primary_theme", "unknown")
                     for item in content_themes.get("items", [])}

        by_platform = defaultdict(lambda: {"views": [], "likes": [], "comments": [], "rates": []})
        by_theme = defaultdict(lambda: {"views": [], "rates": []})

        for item in content_items:
            eng = item.get("engagement", {})
            platform = item.get("platform", "unknown")
            theme = theme_map.get(item.get("id", ""), "unknown")

            by_platform[platform]["views"].append(eng.get("views", 0))
            by_platform[platform]["likes"].append(eng.get("likes", 0))
            by_platform[platform]["comments"].append(eng.get("comments", 0))
            by_platform[platform]["rates"].append(eng.get("engagement_rate", 0))

            by_theme[theme]["views"].append(eng.get("views", 0))
            by_theme[theme]["rates"].append(eng.get("engagement_rate", 0))

        def avg(lst): return round(sum(lst) / len(lst), 4) if lst else 0

        platform_stats = {}
        for p, data in by_platform.items():
            platform_stats[p] = {
                "post_count": len(data["views"]),
                "avg_views": avg(data["views"]),
                "avg_likes": avg(data["likes"]),
                "avg_comments": avg(data["comments"]),
                "avg_engagement_rate": avg(data["rates"]),
                "total_views": sum(data["views"]),
            }

        theme_stats = {
            t: {"avg_views": avg(d["views"]), "avg_engagement_rate": avg(d["rates"]), "post_count": len(d["views"])}
            for t, d in by_theme.items()
        }

        sorted_items = sorted(content_items, key=lambda x: x.get("engagement", {}).get("engagement_rate", 0), reverse=True)
        top_10 = [
            {
                "id": item.get("id", ""),
                "platform": item.get("platform", ""),
                "url": item.get("url", ""),
                "theme": theme_map.get(item.get("id", ""), "unknown"),
                "engagement_rate": item.get("engagement", {}).get("engagement_rate", 0),
                "views": item.get("engagement", {}).get("views", 0),
                "published_at": item.get("published_at", ""),
            }
            for item in sorted_items[:10]
        ]

        total_reach = sum(item.get("engagement", {}).get("views", 0) for item in content_items)

        return {
            "total_post_count": len(content_items),
            "total_estimated_reach": total_reach,
            "by_platform": platform_stats,
            "by_theme": theme_stats,
            "top_10_posts": top_10,
        }
