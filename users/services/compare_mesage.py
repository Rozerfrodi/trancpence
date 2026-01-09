from enum import Enum
from typing import Dict, Any, List


class StabilityLevel(Enum):
    EXCELLENT_IMPROVEMENT = "excellent_improvement"
    GOOD_IMPROVEMENT = "good_improvement"
    SLIGHT_IMPROVEMENT = "slight_improvement"
    STABLE = "stable"
    SLIGHT_DECLINE = "slight_decline"
    MODERATE_DECLINE = "moderate_decline"
    SIGNIFICANT_DECLINE = "significant_decline"
    CRITICAL_DECLINE = "critical_decline"


def get_stability_advice(percent_change: float) -> Dict[str, Any]:
    """
    Returns structured advice for StdDev change.

    Args:
        percent_change: StdDev change in % (negative = improvement)

    Returns:
        JSON-ready dictionary with advice
    """
    abs_change = abs(percent_change)

    # Determine stability level
    if percent_change < -20:
        level = StabilityLevel.EXCELLENT_IMPROVEMENT
    elif percent_change < -10:
        level = StabilityLevel.GOOD_IMPROVEMENT
    elif percent_change < -2:
        level = StabilityLevel.SLIGHT_IMPROVEMENT
    elif percent_change < 2:
        level = StabilityLevel.STABLE
    elif percent_change < 5:
        level = StabilityLevel.SLIGHT_DECLINE
    elif percent_change < 10:
        level = StabilityLevel.MODERATE_DECLINE
    elif percent_change < 20:
        level = StabilityLevel.SIGNIFICANT_DECLINE
    else:
        level = StabilityLevel.CRITICAL_DECLINE

    # Get advice based on level
    advice_map = {
        StabilityLevel.EXCELLENT_IMPROVEMENT: {
            "title": "Outstanding Financial Progress",
            "summary": f"Stability improved by {abs_change}%",
            "key_message": "You've mastered budget control. Consider investments.",
            "actions": [
                "Create passive income sources",
                "Set 5-year financial goals",
                "Consider investment consultation"
            ],
            "icon_code": "crown",
            "color": "#27ae60"
        },
        StabilityLevel.GOOD_IMPROVEMENT: {
            "title": "Great Stability Improvement",
            "summary": f"Stability improved by {abs_change}%",
            "key_message": "Your spending is more predictable. Good for planning.",
            "actions": [
                "Plan major purchases in advance",
                "Increase savings rate by 5-10%",
                "Set annual financial targets"
            ],
            "icon_code": "rocket",
            "color": "#2ecc71"
        },
        StabilityLevel.SLIGHT_IMPROVEMENT: {
            "title": "Stability Improvement",
            "summary": f"Stability improved by {abs_change}%",
            "key_message": "Small positive change. Keep current habits.",
            "actions": [
                "Analyze most stable categories",
                "Set a reward for consistency",
                "Continue current budgeting"
            ],
            "icon_code": "check",
            "color": "#3498db"
        },
        StabilityLevel.STABLE: {
            "title": "Stability Maintained",
            "summary": "No significant changes in spending patterns",
            "key_message": "Financial discipline is consistent. Good baseline.",
            "actions": [
                "Review budget categories",
                "Maintain current savings rate",
                "Consider minor optimizations"
            ],
            "icon_code": "balance",
            "color": "#95a5a6"
        },
        StabilityLevel.SLIGHT_DECLINE: {
            "title": "Minor Stability Decrease",
            "summary": f"Stability decreased by {abs_change}%",
            "key_message": "Small increase in spending variability. Monitor trends.",
            "actions": [
                "Check largest expense categories",
                "Set limits on variable spending",
                "Track expenses for 2 weeks"
            ],
            "icon_code": "warning",
            "color": "#f39c12"
        },
        StabilityLevel.MODERATE_DECLINE: {
            "title": "Moderate Stability Decrease",
            "summary": f"Stability decreased by {abs_change}%",
            "key_message": "Noticeable increase in spending variability. Needs attention.",
            "actions": [
                "Identify irregular large purchases",
                "Create unexpected expenses buffer",
                "Use 24-hour rule for purchases >$100"
            ],
            "icon_code": "alert",
            "color": "#e67e22"
        },
        StabilityLevel.SIGNIFICANT_DECLINE: {
            "title": "Significant Stability Decrease",
            "summary": f"Stability decreased by {abs_change}%",
            "key_message": "High spending variability. Immediate action required.",
            "actions": [
                "Freeze non-essential subscriptions",
                "Use cash-only for 1 week",
                "Consult with financial advisor"
            ],
            "icon_code": "danger",
            "color": "#d35400"
        },
        StabilityLevel.CRITICAL_DECLINE: {
            "title": "Critical Stability Decrease",
            "summary": f"Stability decreased by {abs_change}%",
            "key_message": "Extreme spending variability. Urgent intervention needed.",
            "actions": [
                "Emergency: Essential spending only",
                "Seek professional financial help",
                "Create strict weekly cash budget"
            ],
            "icon_code": "emergency",
            "color": "#c0392b"
        }
    }

    advice = advice_map[level]

    return {
        "stability_level": level.value,
        "percent_change": round(abs_change, 2),
        "title": advice["title"],
        "summary": advice["summary"],
        "key_message": advice["key_message"],
        "actions": advice["actions"],
        "visual": {
            "icon_code": advice["icon_code"],
            "color": advice["color"]
        }
    }


def get_comparison_report(stddev_year1: float, stddev_year2: float) -> Dict[str, Any]:
    """
    Generates complete comparison report for two years.
    """
    # Calculate percentage change
    if stddev_year1 > 0:
        percent_change = ((stddev_year2 - stddev_year1) / stddev_year1) * 100
    else:
        percent_change = 0

    # Get advice
    advice = get_stability_advice(percent_change)

    return {
        "comparison": {
            "year1": {"stddev": round(stddev_year1, 2)},
            "year2": {"stddev": round(stddev_year2, 2)},
            "absolute_difference": round(stddev_year2 - stddev_year1, 2),
            "percent_change": round(percent_change, 2),
            "interpretation": "improvement" if percent_change < 0 else "decline" if percent_change > 0 else "stable"
        },
        "advice": advice,
        "quick_tips": generate_quick_tips(percent_change)
    }


def generate_quick_tips(percent_change: float) -> List[str]:
    """Generates concise actionable tips."""
    abs_change = abs(percent_change)

    if percent_change < -10:
        return [
            "Leverage predictability for investments",
            "Set ambitious financial goals",
            "Share your budgeting success"
        ]
    elif percent_change < -2:
        return [
            "Increase savings rate",
            "Plan major purchases",
            "Review stable categories"
        ]
    elif percent_change < 2:
        return [
            "Maintain current habits",
            "Minor budget optimizations",
            "Regular category review"
        ]
    elif percent_change < 10:
        return [
            "Set spending limits",
            "Track expenses closely",
            "Avoid impulse purchases"
        ]
    else:
        return [
            "Emergency budget review",
            "Essential spending only",
            "Seek professional advice"
        ]