from .layers import ROUTE_COLORS

def build_barangay_popup(brgy_name, routes):
    if not routes:
        return f"<b>{brgy_name}</b><br><i>No routes found</i>"

    all_rows = ""
    for idx, r in enumerate(routes):
        color       = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
        is_remote   = r.get('is_remote', False)
        bg          = "#f9f9f9" if is_remote else ("#f9fffe" if idx == 0 else "white")
        label_color = "#aaa" if is_remote else "#444"
        dist_cell   = "—" if is_remote else f"{r['distance_km']} km"
        time_cell   = "—" if is_remote else f"{r['duration_min']} min"
        dot_color   = "#ccc" if is_remote else color

        all_rows += f"""
        <tr style="border-bottom:1px solid #f0f0f0; background:{bg};">
            <td style="padding:5px 6px; color:{label_color};
                    font-style:{'italic' if is_remote else 'normal'};">
                <span style="color:{dot_color}; font-size:14px;">●</span>
                &nbsp;{r['university']}
            </td>
            <td style="padding:5px 8px; text-align:center;
                    white-space:nowrap; color:{label_color};">
                {dist_cell}
            </td>
            <td style="padding:5px 8px; text-align:center;
                    white-space:nowrap; color:{label_color};">
                {time_cell}
            </td>
            <td style="padding:5px 8px; text-align:center;
                    white-space:nowrap; color:{label_color}; font-size:11px;">
                {r['travel_label']}
            </td>
        </tr>
        """

    return f"""
    <div style="font-family:Arial,sans-serif; width:310px;">
        <div style="background:#185FA5; color:white;
                    padding:8px 12px; border-radius:4px 4px 0 0;
                    position:sticky; top:0;">
            <b>{brgy_name}</b>
            <span style="font-size:10px; opacity:0.8; float:right; margin-top:2px;">
                driving · {len(routes)} universities
            </span>
        </div>
        <div style="max-height:220px; overflow-y:auto;
                    border:1px solid #e0e0e0; border-top:none;
                    border-radius:0 0 4px 4px;">
            <table style="border-collapse:collapse; width:100%; font-size:12px;">
                <thead style="position:sticky; top:0; z-index:1;">
                    <tr style="background:#f0f4f8;">
                        <th style="padding:4px 6px; text-align:left;
                                   font-weight:600; color:#555;
                                   border-bottom:1px solid #ddd;">University</th>
                        <th style="padding:4px 8px; font-weight:600;
                                   color:#555; border-bottom:1px solid #ddd;">km</th>
                        <th style="padding:4px 8px; font-weight:600;
                                   color:#555; border-bottom:1px solid #ddd;">min</th>
                        <th style="padding:4px 8px; font-weight:600;
                                   color:#555; border-bottom:1px solid #ddd;">rides</th>
                    </tr>
                </thead>
                <tbody>{all_rows}</tbody>
            </table>
        </div>
        <div style="font-size:10px; color:#aaa; padding:5px 6px; text-align:right;">
            shortest first &nbsp;|&nbsp; scroll for more &nbsp;|&nbsp;
            click map to clear routes
        </div>
    </div>
    """

def build_tooltip(brgy_name, routes):
    if not routes:
        return brgy_name
    nearest = routes[0]
    return (
        f"<b>{brgy_name}</b><br>"
        f"Nearest: <b>{nearest['university']}</b><br>"
        f"{nearest['distance_km']} km · {nearest['duration_min']} min"
    )