"""
OpenStreetMap / Folium map helper for Volunite.

Generates Folium maps with Leaflet/OSM tiles and cluster markers
colour-coded by category. 100% free, no API key required.
"""

import html
import json
import os
from typing import List, Dict, Any
from urllib.parse import quote


# Category to color mapping for map markers (Vibrant Premium Palette)
CATEGORY_COLORS = {
    "healthcare": "#f43f5e",   # Rose
    "food": "#f59e0b",         # Amber
    "education": "#3b82f6",    # Blue
    "sanitation": "#10b981",   # Emerald
    "employment": "#a855f7",   # Purple
}

CATEGORY_ICONS = {
    "healthcare": "🏥",
    "food": "🍚",
    "education": "📚",
    "sanitation": "🚿",
    "employment": "💼",
}


def generate_folium_map(clusters: List[Dict[str, Any]], surveys: List[Dict[str, Any]] = None) -> object:
    """
    Generate a premium Folium map with cluster markers and survey points.
    """
    import folium
    from folium import plugins

    # Centre on Maharashtra
    center_lat = 18.5204
    center_lng = 73.8567
    
    # Use CartoDB Dark Matter for a high-end look
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=7,
        tiles='CartoDB dark_matter',
        attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors | Volunite Intelligence",
    )

    # Add cluster markers
    for cluster in clusters:
        centroid = cluster.get("centroid", {})
        lat = centroid.get("lat", center_lat)
        lng = centroid.get("lng", center_lng)
        top_category = cluster.get("top_category", "healthcare")
        count = cluster.get("count", 0)
        total_urgency = cluster.get("total_urgency", 0)
        color = CATEGORY_COLORS.get(top_category, "#00BFA5")
        icon_emoji = CATEGORY_ICONS.get(top_category, "📍")
        safe_cat = html.escape(str(top_category).upper(), quote=True)

        popup_html = f"""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; min-width: 220px; background: #0f172a; color: #f8fafc; padding: 15px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <div style="background: {color}22; padding: 8px; border-radius: 12px; font-size: 20px;">{icon_emoji}</div>
                <div>
                    <p style="margin: 0; font-size: 10px; font-weight: 800; color: {color}; letter-spacing: 1.5px;">CLUSTER #{cluster.get('cluster_id', 0) + 1}</p>
                    <h4 style="margin: 0; font-weight: 800; font-size: 16px;">{safe_cat}</h4>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
                <div>
                    <p style="margin: 0; font-size: 9px; font-weight: 700; color: #64748b; text-transform: uppercase;">Needs</p>
                    <p style="margin: 2px 0 0 0; font-weight: 800; font-size: 18px;">{count}</p>
                </div>
                <div>
                    <p style="margin: 0; font-size: 9px; font-weight: 700; color: #64748b; text-transform: uppercase;">Urgency</p>
                    <p style="margin: 2px 0 0 0; font-weight: 800; font-size: 18px;">{total_urgency:.1f}</p>
                </div>
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lng],
            radius=max(10, min(count * 4, 35)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{icon_emoji} {str(top_category).title()} — {count} needs",
        ).add_to(m)

    # Add individual survey markers if provided
    if surveys:
        marker_cluster = plugins.MarkerCluster(
            name="Individual Surveys",
            overlay=True,
            control=True,
            icon_create_function=None
        ).add_to(m)
        
        for s in surveys:
            loc = s.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            if lat and lng:
                cat = s.get("category", "healthcare")
                color = CATEGORY_COLORS.get(cat, "#00BFA5")
                desc = str(s.get("description", ""))[:80]
                popup_html = f"""
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; padding: 10px; min-width: 150px;">
                    <p style="margin: 0; font-weight: 800; color: {color}; font-size: 12px;">{str(cat).upper()}</p>
                    <p style="margin: 4px 0; font-size: 11px; line-height: 1.4; color: #334155;">{html.escape(desc, quote=True)}...</p>
                    <div style="display: flex; justify-content: space-between; font-size: 10px; font-weight: 700; color: #64748b; margin-top: 8px;">
                        <span>{html.escape(str(s.get('district', 'N/A')), quote=True)}</span>
                        <span style="color: {color}">⭐ {s.get('severity', 0)}</span>
                    </div>
                </div>
                """
                folium.CircleMarker(
                    location=[lat, lng],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.6,
                    weight=1,
                    popup=folium.Popup(popup_html, max_width=250),
                ).add_to(marker_cluster)

    # Add layer control
    folium.LayerControl(position='topright', collapsed=True).add_to(m)

    return m


def generate_map_html(clusters: List[Dict[str, Any]], api_key: str = "") -> str:
    """
    Generate standalone Google Maps HTML embed with cluster markers.

    Args:
        clusters: List of cluster dictionaries.
        api_key: Google Maps JavaScript API key.

    Returns:
        HTML string for embedding in an iframe.
    """
    if not api_key:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")

    markers_js = ""
    for cluster in clusters:
        centroid = cluster.get("centroid", {})
        lat = centroid.get("lat", 18.5)
        lng = centroid.get("lng", 74.0)
        top_category = cluster.get("top_category", "healthcare")
        count = cluster.get("count", 0)
        total_urgency = cluster.get("total_urgency", 0)
        color = CATEGORY_COLORS.get(top_category, "#718096")
        title = f"{str(top_category).title()} — {count} needs (Urgency: {total_urgency:.1f})"

        markers_js += f"""
        new google.maps.Marker({{
            position: {{ lat: {lat}, lng: {lng} }},
            map: map,
            title: {json.dumps(title)},
            icon: {{
                path: google.maps.SymbolPath.CIRCLE,
                scale: {max(8, min(count * 3, 20))},
                fillColor: '{color}',
                fillOpacity: 0.8,
                strokeWeight: 2,
                strokeColor: '#ffffff',
            }},
        }});
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #map {{ width: 100%; height: 500px; border-radius: 12px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            function initMap() {{
                const map = new google.maps.Map(document.getElementById('map'), {{
                    center: {{ lat: 18.5, lng: 74.0 }},
                    zoom: 7,
                    styles: [
                        {{ elementType: 'geometry', stylers: [{{ color: '#1a1a2e' }}] }},
                        {{ elementType: 'labels.text.fill', stylers: [{{ color: '#8a8a8a' }}] }},
                        {{ featureType: 'water', elementType: 'geometry', stylers: [{{ color: '#0f3460' }}] }},
                    ],
                }});
                {markers_js}
            }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={quote(api_key, safe='')}&callback=initMap" async defer></script>
    </body>
    </html>
    """
    return html
