import asyncio
import base64
from datetime import datetime
import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Authorized fallback dataset matching the LiveWave TV UI mockup
AUTHORIZED_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Sports",
        "image": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=300&q=80",
        "channel_count": 112,
    },
    {
        "id": 2,
        "name": "Movies",
        "image": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=300&q=80",
        "channel_count": 54,
    },
    {
        "id": 3,
        "name": "News",
        "image": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=300&q=80",
        "channel_count": 48,
    },
    {
        "id": 4,
        "name": "Kids",
        "image": "https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=300&q=80",
        "channel_count": 32,
    },
    {
        "id": 5,
        "name": "Entertainment",
        "image": "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=300&q=80",
        "channel_count": 67,
    },
    {
        "id": 6,
        "name": "Documentary",
        "image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300&q=80",
        "channel_count": 28,
    },
    {
        "id": 7,
        "name": "Music",
        "image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&q=80",
        "channel_count": 24,
    },
    {
        "id": 8,
        "name": "Religious",
        "image": "https://images.unsplash.com/photo-1544427920-c49ccfb85579?w=300&q=80",
        "channel_count": 16,
    },
]

# Today's premier live football matches & game fixtures
TODAY_MATCHES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "home_team": "Real Madrid",
        "away_team": "FC Barcelona",
        "home_logo": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=100&q=80",
        "away_logo": "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=100&q=80",
        "tournament": "La Liga • El Clásico",
        "match_time": "LIVE",
        "status": "live",
        "score": "2 - 1",
        "minute": "68'",
        "channel_id": 101,
        "channel_name": "beIN Sports 1",
    },
    {
        "id": 2,
        "home_team": "Manchester City",
        "away_team": "Liverpool",
        "home_logo": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=100&q=80",
        "away_logo": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=100&q=80",
        "tournament": "Premier League",
        "match_time": "LIVE",
        "status": "live",
        "score": "1 - 1",
        "minute": "54'",
        "channel_id": 104,
        "channel_name": "Sky Sports Premier League",
    },
    {
        "id": 3,
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "home_logo": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=100&q=80",
        "away_logo": "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=100&q=80",
        "tournament": "Premier League",
        "match_time": "20:00 GMT",
        "status": "upcoming",
        "score": "- : -",
        "minute": None,
        "channel_id": 105,
        "channel_name": "BT Sport 1",
    },
    {
        "id": 4,
        "home_team": "Paris SG",
        "away_team": "Bayern Munich",
        "home_logo": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=100&q=80",
        "away_logo": "https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=100&q=80",
        "tournament": "UEFA Champions League",
        "match_time": "21:00 GMT",
        "status": "upcoming",
        "score": "- : -",
        "minute": None,
        "channel_id": 108,
        "channel_name": "RMC Sport",
    },
    {
        "id": 5,
        "home_team": "AC Milan",
        "away_team": "Inter Milan",
        "home_logo": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=100&q=80",
        "away_logo": "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=100&q=80",
        "tournament": "Serie A • Derby della Madonnina",
        "match_time": "20:45 GMT",
        "status": "upcoming",
        "score": "- : -",
        "minute": None,
        "channel_id": 102,
        "channel_name": "beIN Sports 2",
    },
]

# Verified, DRM-free playable test streams for ExoPlayer
AUTHORIZED_CHANNELS: Dict[int, Dict[str, Any]] = {

    101: {
        "id": 101,
        "category_id": 1,
        "name": "beIN Sports 1",
        "logo": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=150&q=80",
        "description": "Live football, tennis, basketball and international athletic competitions.",
        "is_live": True,
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [
            {
                "url": "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
                "format": "hls",
                "quality": "auto",
            }
        ],
    },
    102: {
        "id": 102,
        "category_id": 1,
        "name": "beIN Sports 2",
        "logo": "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=150&q=80",
        "description": "European football league highlights, analysis and live studio matches.",
        "is_live": True,
        "stream_url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    103: {
        "id": 103,
        "category_id": 1,
        "name": "ESPN",
        "logo": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=150&q=80",
        "description": "Worldwide leader in sports coverage, news, scores, and live games.",
        "is_live": True,
        "stream_url": "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    104: {
        "id": 104,
        "category_id": 1,
        "name": "Sky Sports Premier League",
        "logo": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=150&q=80",
        "description": "Exclusive live English Premier League fixtures, highlights, and expert commentary.",
        "is_live": True,
        "stream_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    105: {
        "id": 105,
        "category_id": 1,
        "name": "BT Sport 1",
        "logo": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=150&q=80",
        "description": "Champions League football, rugby union, motorsport and combat sports.",
        "is_live": True,
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    106: {
        "id": 106,
        "category_id": 1,
        "name": "Eurosport 1",
        "logo": "https://images.unsplash.com/photo-1517649763962-0c623266ddc0?w=150&q=80",
        "description": "Grand Slam tennis, cycling tours, Olympic disciplines and winter sports.",
        "is_live": True,
        "stream_url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    107: {
        "id": 107,
        "category_id": 1,
        "name": "DAZN",
        "logo": "https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=150&q=80",
        "description": "Live championship boxing, mixed martial arts, and global fighting events.",
        "is_live": True,
        "stream_url": "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    108: {
        "id": 108,
        "category_id": 1,
        "name": "RMC Sport",
        "logo": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=150&q=80",
        "description": "European football, combat sports nights, and exclusive sporting documentaries.",
        "is_live": True,
        "stream_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    201: {
        "id": 201,
        "category_id": 2,
        "name": "Cinema Premiere HD",
        "logo": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=150&q=80",
        "description": "Blockbuster Hollywood movies, 4K film premieres, and cinema classics.",
        "is_live": True,
        "stream_url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    202: {
        "id": 202,
        "category_id": 2,
        "name": "Action Movies Plus",
        "logo": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=150&q=80",
        "description": "24/7 non-stop action, thrillers, sci-fi and martial arts cinema.",
        "is_live": True,
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    301: {
        "id": 301,
        "category_id": 3,
        "name": "BBC News World",
        "logo": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=150&q=80",
        "description": "Trusted global breaking news, in-depth reports, weather and business updates.",
        "is_live": True,
        "stream_url": "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    302: {
        "id": 302,
        "category_id": 3,
        "name": "Sky News 24/7",
        "logo": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=150&q=80",
        "description": "First for breaking news, eyewitness reports and live global press conferences.",
        "is_live": True,
        "stream_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    401: {
        "id": 401,
        "category_id": 4,
        "name": "Cartoon Network",
        "logo": "https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&q=80",
        "description": "Fun animations, teen favorites, comedy cartoons and classic animated shorts.",
        "is_live": True,
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    501: {
        "id": 501,
        "category_id": 5,
        "name": "TF1",
        "logo": "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=150&q=80",
        "description": "Prime entertainment, reality shows, evening drama and variety series.",
        "is_live": True,
        "stream_url": "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    601: {
        "id": 601,
        "category_id": 6,
        "name": "Discovery Channel",
        "logo": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=150&q=80",
        "description": "Science, technology, exploration, nature and deep-sea documentaries.",
        "is_live": True,
        "stream_url": "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    701: {
        "id": 701,
        "category_id": 7,
        "name": "MTV Live",
        "logo": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&q=80",
        "description": "Live music festivals, global top 40 video charts and concert performances.",
        "is_live": True,
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
    801: {
        "id": 801,
        "category_id": 8,
        "name": "Peace TV",
        "logo": "https://images.unsplash.com/photo-1544427920-c49ccfb85579?w=150&q=80",
        "description": "Spiritual lectures, religious guidance, moral education and recitations.",
        "is_live": True,
        "stream_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8",
        "stream_format": "hls",
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
        "backup_streams": [],
    },
}


def build_channel_epg(channel_id: int, channel_name: str, category_id: int = 1) -> Dict[str, Any]:
    """Generates real-time 24-hour EPG programs dynamically mapped to the current time."""
    now = datetime.now()
    cur_mins = now.hour * 60 + now.minute

    ch_lower = channel_name.lower()
    if category_id == 1 or "sport" in ch_lower or "bein" in ch_lower or "espn" in ch_lower:
        template = [
            ("06:00", "08:30", "Morning Kick-Off & Football Round-Up", "Worldwide sports highlights, overnight scores, and daily transfer news.", "Sports"),
            ("08:30", "11:00", "Premier League Classics • Historic Encounters", "Relive the greatest football matches in Premier League and European history.", "Sports"),
            ("11:00", "13:30", "Champions League Studio • Tactics & Form", "Comprehensive tactical preview with elite football pundits.", "Sports"),
            ("13:30", "16:00", "Matchday Live Countdown", "Live pitchside reporting, confirmed lineups, and warm-up coverage.", "Sports"),
            ("16:00", "18:30", f"⚽ LIVE: {channel_name} Main Event", f"Full live coverage of prime fixture with real-time commentary on {channel_name}.", "Sports"),
            ("18:30", "20:30", "🏆 Post-Match Extra • Press Conferences & Highlights", "Manager interviews, controversial decisions review, and match stats.", "Sports"),
            ("20:30", "23:00", "⚽ LIVE: Primetime Football Clash", "Evening featured league match live with 4K stream feed.", "Sports"),
            ("23:00", "06:00", "Late Night Sports Replay & Best Goals", "Comprehensive round-up of all goals, saves, and top moments from the day.", "Sports"),
        ]
    elif category_id == 2 or "cinema" in ch_lower or "movie" in ch_lower:
        template = [
            ("06:00", "08:30", "Classic Cinema: Casablanca", "Golden age classic Hollywood romance starring Humphrey Bogart.", "Movies"),
            ("08:30", "11:00", "Action Thriller: Mad Max Fury Road", "Post-apocalyptic high-octane pursuit across the desert wasteland.", "Movies"),
            ("11:00", "13:30", "Sci-Fi Prime: Dune (Part One)", "Paul Atreides travels to the most dangerous planet in the universe.", "Movies"),
            ("13:30", "16:00", "🎬 Blockbuster: Inception [4K HDR]", "Dom Cobb infiltrates dreams to plant an idea in a corporate heir.", "Movies"),
            ("16:00", "18:30", "🎬 Cinema Premiere: Interstellar [IMAX]", "A team of explorers travels through a wormhole in search of a new home.", "Movies"),
            ("18:30", "21:00", "🎬 Featured Epic: The Dark Knight [4K]", "Batman faces his ultimate psychological test against the Joker.", "Movies"),
            ("21:00", "23:30", "🎬 Evening Film: Oppenheimer", "The story of American scientist J. Robert Oppenheimer and the Manhattan Project.", "Movies"),
            ("23:30", "06:00", "Midnight Movie Marathon: Sci-Fi & Mystery", "Late night double-feature of cult classics and acclaimed thrillers.", "Movies"),
        ]
    elif category_id == 3 or "news" in ch_lower:
        template = [
            ("06:00", "09:00", "Global Morning News Live", "Top international news, weather forecasting, and market opening bell.", "News"),
            ("09:00", "12:00", "World Business & Financial Markets", "Stock markets, tech trends, commodities and financial analysis.", "News"),
            ("12:00", "14:00", "Midday World Briefing", "Live reporting from correspondents across Europe, Americas and Asia.", "News"),
            ("14:00", "17:00", "Special Investigative Report", "Deep investigative journalism focusing on geopolitical and economic shifts.", "News"),
            ("17:00", "19:00", "🌍 Live News Hour at Five", "In-depth global stories, live interviews with ambassadors and leaders.", "News"),
            ("19:00", "21:00", "The Evening Debate", "Heated discussions on the most pressing issues of current affairs.", "News"),
            ("21:00", "23:00", "Nightline International", "A wrap of the day's major events and in-depth cultural reports.", "News"),
            ("23:00", "06:00", "Global News 24/7 Live Stream", "Continuous breaking news updates from global bureaus.", "News"),
        ]
    elif category_id == 4 or "kid" in ch_lower or "cartoon" in ch_lower:
        template = [
            ("06:00", "08:30", "Morning Toons: Tom & Jerry Classics", "The classic rivalry between the cat and mouse.", "Kids"),
            ("08:30", "11:00", "🎨 Teen Titans Go! • Superhero Mayhem", "Robin, Starfire, Cyborg, Raven and Beast Boy defend Jump City.", "Kids"),
            ("11:00", "13:30", "🐱 The Amazing World of Gumball", "Gumball and Darwin's misadventures in the town of Elmore.", "Kids"),
            ("13:30", "16:00", "SpongeBob SquarePants Marathon", "Fun undersea adventures in Bikini Bottom with SpongeBob and Patrick.", "Kids"),
            ("16:00", "18:30", "⚔️ Adventure Time: Distant Lands", "Finn the Human and Jake the Dog explore the magical Land of Ooo.", "Kids"),
            ("18:30", "21:00", "Family Animation Night: The Incredibles", "A family of superheroes tries to live a quiet suburban life.", "Kids"),
            ("21:00", "06:00", "Lullaby & Classic Cartoons", "Gentle animations and bedtime stories for children.", "Kids"),
        ]
    else:
        template = [
            ("06:00", "09:00", "Morning Discovery & Nature", "Exploring the wonders of wildlife, geography, and ecosystems.", "Documentary"),
            ("09:00", "12:00", "Extreme Planet: Earth Frontiers", "Volcanoes, deep sea trenches, and weather extremes around Earth.", "Documentary"),
            ("12:00", "15:00", "Secrets of Ancient Civilizations", "Archaeological excavations revealing mysteries of Egypt and Rome.", "History"),
            ("15:00", "18:00", "🦁 Predators of the African Savannah", "Lions, cheetahs, and leopards navigating survival on the Serengeti.", "Nature"),
            ("18:00", "21:00", "🌊 Mysteries of the Deep Ocean [4K]", "Exploring the Mariana Trench and bioluminescent deep-sea life.", "Science"),
            ("21:00", "00:00", "Cosmos: Journey Through the Universe", "Astrophysics, black holes, and the future of human space exploration.", "Space"),
            ("00:00", "06:00", "Nighttime Ambient Soundscapes & Earth Views", "Soothing visuals and natural sounds from around the globe.", "Relaxation"),
        ]

    schedule = []
    current_prog = None
    next_prog = None

    for idx, (start_str, end_str, title, desc, cat) in enumerate(template):
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        start_min = sh * 60 + sm
        end_min = eh * 60 + em
        if end_min <= start_min:
            end_min += 24 * 60

        test_cur = cur_mins
        if cur_mins < start_min and end_min > 24 * 60:
            test_cur += 24 * 60

        is_live = False
        progress = 0
        time_rem = None

        if start_min <= test_cur < end_min:
            is_live = True
            dur = max(1, end_min - start_min)
            elapsed = test_cur - start_min
            progress = min(100, max(0, int((elapsed / dur) * 100)))
            remaining_mins = max(1, end_min - test_cur)
            time_rem = f"{remaining_mins}m left"

        prog_item = {
            "id": channel_id * 100 + idx + 1,
            "title": title,
            "description": desc,
            "start_time": start_str,
            "end_time": end_str,
            "progress_percent": progress,
            "is_live": is_live,
            "category": cat,
            "time_remaining": time_rem,
        }
        schedule.append(prog_item)

        if is_live:
            current_prog = prog_item

    if current_prog:
        cur_idx = schedule.index(current_prog)
        if cur_idx + 1 < len(schedule):
            next_prog = schedule[cur_idx + 1]
        else:
            next_prog = schedule[0]
    elif schedule:
        current_prog = schedule[0]
        next_prog = schedule[1] if len(schedule) > 1 else None

    return {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "current_program": current_prog,
        "next_program": next_prog,
        "schedule": schedule,
    }


class UpstreamClient:
    """Enhanced client for upstream YacineTV with mirror failover, multi-key decryption, search, and resilient fallback."""

    def __init__(self):
        self.base_url = settings.upstream_base_url.rstrip("/")
        self.mirrors = [m.rstrip("/") for m in settings.upstream_mirrors]
        self.keys = settings.upstream_keys
        self.timeout = settings.upstream_timeout_seconds
        self.probe_timeout = settings.stream_probe_timeout_seconds
        self._active_mirror: Optional[str] = None
        self._upstream_offline_until: float = 0.0

    def decrypt(self, enc: str, key: str) -> str:
        """Decrypts base64 encoded and XOR-masked payload."""
        try:
            decoded = base64.b64decode(enc.encode("ascii")).decode("ascii")
            result = []
            key_len = len(key)
            for i in range(len(decoded)):
                result.append(chr(ord(decoded[i]) ^ ord(key[i % key_len])))
            return "".join(result)
        except Exception as e:
            logger.debug(f"Decryption failed with key: {e}")
            raise ValueError(f"Payload decryption failed: {e}")

    def decrypt_with_keys(self, enc: str, timestamp: str) -> Optional[Any]:
        """Tries all configured XOR keys to parse valid JSON payload."""
        for candidate_key in self.keys:
            try:
                full_key = candidate_key + timestamp
                decrypted = self.decrypt(enc, full_key)
                return json.loads(decrypted)
            except Exception:
                continue
        return None

    async def _fetch_from_url(self, base: str, path: str) -> Optional[Any]:
        """Attempts to fetch and decrypt from a specific mirror."""
        url = f"{base}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    url,
                    headers={
                        "User-Agent": "LiveWaveTV/1.1 (Android; ExoPlayer)",
                        "Accept": "*/*",
                    },
                )
                if r.status_code != 200:
                    return None

                # Must not be HTML parking/sedo page
                if "<html" in r.text.lower() or "<!doctype" in r.text.lower():
                    return None

                timestamp = r.headers.get("t", str(int(time.time())))
                parsed = self.decrypt_with_keys(r.text, timestamp)
                if parsed is not None:
                    self._active_mirror = base
                    return parsed
        except Exception as e:
            logger.debug(f"Fetch failed for {url}: {e}")
        return None

    async def _fetch_from_url_fast(self, base: str, path: str) -> Optional[Any]:
        """Fast timeout fetcher for mirror pool probing."""
        url = f"{base}{path}"
        try:
            async with httpx.AsyncClient(timeout=1.2) as client:
                r = await client.get(
                    url,
                    headers={
                        "User-Agent": "LiveWaveTV/1.1 (Android; ExoPlayer)",
                        "Accept": "*/*",
                    },
                )
                if r.status_code != 200 or "<html" in r.text.lower() or "<!doctype" in r.text.lower():
                    return None
                timestamp = r.headers.get("t", str(int(time.time())))
                parsed = self.decrypt_with_keys(r.text, timestamp)
                if parsed is not None:
                    self._active_mirror = base
                    return parsed
        except Exception:
            pass
        return None

    async def _fetch_upstream(self, path: str) -> Optional[Any]:
        """Fetches from active mirror or concurrently tests mirror pool with circuit breaker."""
        now = time.time()
        if now < self._upstream_offline_until:
            return None

        # 1. Try active mirror if already known
        if self._active_mirror:
            data = await self._fetch_from_url_fast(self._active_mirror, path)
            if data is not None:
                return data

        # 2. Concurrently test unique mirrors with tight timeout
        unique_mirrors = list(dict.fromkeys([self.base_url] + self.mirrors))
        tasks = [self._fetch_from_url_fast(m, path) for m in unique_mirrors]
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if res and not isinstance(res, Exception):
                    return res
        except Exception:
            pass

        # Trip circuit breaker for 60 seconds so fallback responses are instantaneous
        self._upstream_offline_until = now + 60.0
        return None

    async def check_upstream_health_detailed(self) -> Dict[str, Any]:
        """Probes all mirrors and returns comprehensive status report."""
        tested = []
        is_any_working = False

        mirrors_to_test = list(dict.fromkeys([self.base_url] + self.mirrors))
        for m in mirrors_to_test:
            start = time.perf_counter()
            reachable = False
            status_code = None
            try:
                async with httpx.AsyncClient(timeout=2.5) as client:
                    r = await client.get(f"{m}/api/categories")
                    status_code = r.status_code
                    if r.status_code == 200 and "<html" not in r.text.lower():
                        timestamp = r.headers.get("t", str(int(time.time())))
                        if self.decrypt_with_keys(r.text, timestamp) is not None:
                            reachable = True
                            is_any_working = True
                            self._active_mirror = m
            except Exception:
                reachable = False

            latency = round((time.perf_counter() - start) * 1000, 1)
            tested.append({
                "mirror": m,
                "reachable": reachable,
                "status_code": status_code,
                "latency_ms": latency,
            })

        return {
            "upstream_available": is_any_working,
            "active_mirror": self._active_mirror,
            "tested_mirrors": tested,
        }

    async def check_upstream_health(self) -> bool:
        """Quick boolean check if upstream responds."""
        detailed = await self.check_upstream_health_detailed()
        return detailed["upstream_available"]

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Fetch categories from upstream or fallback catalog."""
        upstream_data = await self._fetch_upstream("/api/categories")
        if upstream_data and isinstance(upstream_data, list):
            return [
                {
                    "id": item.get("id", idx + 1),
                    "name": item.get("name", f"Category {idx + 1}"),
                    "image": item.get("image") or item.get("logo"),
                    "channel_count": item.get("channels_count", 0),
                }
                for idx, item in enumerate(upstream_data)
            ]

        if settings.enable_authorized_fallback:
            return AUTHORIZED_CATEGORIES

        return []

    async def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific category."""
        categories = await self.get_categories()
        for cat in categories:
            if cat["id"] == category_id:
                return cat
        return None

    async def get_category_channels(self, category_id: int) -> List[Dict[str, Any]]:
        """Get channel list for a specific category."""
        upstream_data = await self._fetch_upstream(f"/api/categories/{category_id}/channels")
        if upstream_data and isinstance(upstream_data, list):
            return [
                {
                    "id": item.get("id"),
                    "category_id": category_id,
                    "name": item.get("name", "Channel"),
                    "logo": item.get("logo") or item.get("image"),
                    "description": item.get("description"),
                    "is_live": True,
                    "stream_format": "hls",
                }
                for item in upstream_data
            ]

        if settings.enable_authorized_fallback:
            result = []
            for ch in AUTHORIZED_CHANNELS.values():
                if ch["category_id"] == category_id:
                    epg_info = build_channel_epg(ch["id"], ch["name"], category_id)
                    cur_p = epg_info.get("current_program")
                    result.append({
                        "id": ch["id"],
                        "category_id": ch["category_id"],
                        "name": ch["name"],
                        "logo": ch["logo"],
                        "description": ch["description"],
                        "is_live": ch["is_live"],
                        "stream_format": ch["stream_format"],
                        "current_program": f"{cur_p['title']} ({cur_p['time_remaining']})" if cur_p else None,
                        "current_program_time": f"{cur_p['start_time']} - {cur_p['end_time']}" if cur_p else None,
                        "current_program_progress": cur_p["progress_percent"] if cur_p else 0,
                    })
            return result

        return []

    async def get_all_channels(self) -> List[Dict[str, Any]]:
        """Returns all channels across all categories."""
        all_channels = []
        categories = await self.get_categories()
        for cat in categories:
            cat_channels = await self.get_category_channels(cat["id"])
            all_channels.extend(cat_channels)
        return all_channels

    async def search_channels(
        self, query: str, category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Searches channels by query string and optional category filter."""
        q = query.strip().lower()
        if category_id:
            channels = await self.get_category_channels(category_id)
        else:
            channels = await self.get_all_channels()

        if not q:
            return channels

        return [
            ch for ch in channels
            if q in ch["name"].lower() or (ch.get("description") and q in ch["description"].lower())
        ]

    async def get_channel_detail(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Get playable channel detail with resolved stream URLs and real-time program info."""
        upstream_data = await self._fetch_upstream(f"/api/channel/{channel_id}")
        if upstream_data and isinstance(upstream_data, dict):
            epg_info = build_channel_epg(channel_id, upstream_data.get("name", "Channel"), upstream_data.get("category_id", 1))
            cur_p = epg_info.get("current_program")
            return {
                "id": upstream_data.get("id", channel_id),
                "category_id": upstream_data.get("category_id", 1),
                "name": upstream_data.get("name", "Channel"),
                "logo": upstream_data.get("logo"),
                "description": upstream_data.get("description"),
                "is_live": True,
                "stream_url": upstream_data.get("url"),
                "stream_format": "hls",
                "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"},
                "backup_streams": [],
                "current_program": f"{cur_p['title']} ({cur_p['time_remaining']})" if cur_p else None,
                "current_program_time": f"{cur_p['start_time']} - {cur_p['end_time']}" if cur_p else None,
                "current_program_progress": cur_p["progress_percent"] if cur_p else 0,
            }

        if settings.enable_authorized_fallback:
            ch = AUTHORIZED_CHANNELS.get(channel_id)
            if ch:
                detail = dict(ch)
                epg_info = build_channel_epg(channel_id, ch["name"], ch.get("category_id", 1))
                cur_p = epg_info.get("current_program")
                if cur_p:
                    detail["current_program"] = f"{cur_p['title']} ({cur_p['time_remaining']})"
                    detail["current_program_time"] = f"{cur_p['start_time']} - {cur_p['end_time']}"
                    detail["current_program_progress"] = cur_p["progress_percent"]
                return detail

        return None

    async def get_channel_epg(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Returns the real-time program guide (EPG) for a specific channel."""
        ch = await self.get_channel_detail(channel_id)
        if not ch:
            return None
        return build_channel_epg(channel_id, ch["name"], ch.get("category_id", 1))

    async def get_all_epg(self) -> List[Dict[str, Any]]:
        """Returns current live programs and upcoming schedules across all channels."""
        channels = await self.get_all_channels()
        return [
            build_channel_epg(ch["id"], ch["name"], ch.get("category_id", 1))
            for ch in channels
        ]

    async def probe_stream(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Probes the live stream endpoint of a channel for latency and validity."""
        channel = await self.get_channel_detail(channel_id)
        if not channel or not channel.get("stream_url"):
            return None

        stream_url = channel["stream_url"]
        start_time = time.perf_counter()
        is_reachable = False
        http_status = None
        content_type = None
        is_hls = ".m3u8" in stream_url.lower()

        try:
            headers = channel.get("headers") or {"User-Agent": "LiveWaveTV-ExoPlayer/1.0"}
            async with httpx.AsyncClient(timeout=self.probe_timeout, follow_redirects=True) as client:
                # Issue GET request with small range for quick header examination
                headers["Range"] = "bytes=0-1024"
                res = await client.get(stream_url, headers=headers)
                http_status = res.status_code
                content_type = res.headers.get("content-type")
                if http_status in (200, 206):
                    is_reachable = True
                    if content_type and ("mpegurl" in content_type.lower() or "vnd.apple" in content_type.lower()):
                        is_hls = True
        except Exception as e:
            logger.debug(f"Stream probe failed for {stream_url}: {e}")

        latency = round((time.perf_counter() - start_time) * 1000, 1)

        return {
            "channel_id": channel_id,
            "channel_name": channel["name"],
            "stream_url": stream_url,
            "is_reachable": is_reachable,
            "http_status": http_status,
            "latency_ms": latency,
            "content_type": content_type,
            "is_hls": is_hls,
            "checked_at": time.time(),
        }

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Returns today's live sports games and fixtures."""
        return TODAY_MATCHES


upstream_client = UpstreamClient()

