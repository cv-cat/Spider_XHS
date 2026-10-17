"""Creator 4.3.6 signing state with explicit browser-derived inputs.

The algorithms live in :mod:`xhs_utils.xhs_core`; this module owns only the
Creator release, page lifecycle and environment material.  No browser object is
read at runtime.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


_REFERENCE_PATH = Path(__file__).with_name('js') / 'reference_profile.json'
REFERENCE_PROFILE = json.loads(_REFERENCE_PATH.read_text(encoding='utf-8'))
DS_REFRESH_INTERVAL_MS = 15 * 60 * 1000

_DOCUMENT_COOKIE_ORDER = (
    'ets', 'a1', 'webId', 'gid', 'abRequestId', 'webBuild', 'xsecappid',
    'websectiga', 'sec_poison_id', 'loadts',
)


def now_ms() -> int:
    return int(time.time() * 1000)


def parse_cookie_kv(value: Any) -> Dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {
            str(key): str(item)
            for key, item in value.items()
            if key is not None and item is not None
        }
    result: Dict[str, str] = {}
    for part in str(value).split(';'):
        item = part.strip()
        if not item:
            continue
        key, separator, content = item.partition('=')
        if key:
            result[key.strip()] = content if separator else ''
    return result


def cookie_header(value: Any) -> str:
    return '; '.join(
        f'{key}={item}' for key, item in parse_cookie_kv(value).items()
    )


def document_cookie_header(value: Any) -> str:
    """Build the exact Cookie view used by Creator fingerprint field ``x57``.

    HttpOnly login tokens are deliberately excluded.  The allow-list is based
    on the decoded Creator browser profile and prevents a copied full Cookie
    from leaking authentication tokens into ``profileData``.
    """
    values = parse_cookie_kv(value)
    return '; '.join(
        f'{key}={values[key]}'
        for key in _DOCUMENT_COOKIE_ORDER
        if values.get(key) is not None and key in values
    )


def _tail_bytes(value: Any) -> Tuple[int, ...]:
    if isinstance(value, str):
        raw = bytes.fromhex(value)
    else:
        raw = bytes(int(item) & 0xff for item in value)
    if len(raw) != 14:
        raise ValueError(f'Creator MNS envFpTail must be 14 bytes, got {len(raw)}')
    return tuple(raw)


def _js_atom(value: Any) -> str:
    if value is None:
        return 'null'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if isinstance(value, float) and value.is_integer():
        # JS String(整数浮点) 不带 .0（浏览器 x84 的 to 即如此）
        return str(int(value))
    return str(value)


def _map_text(value: Mapping[str, Any]) -> str:
    return ','.join(f'{key}:{_js_atom(item)}' for key, item in value.items())


@dataclass(frozen=True)
class CreatorMnsMaterial:
    tier: str
    device_tag: str
    env_const: int
    env_fp_tail: Tuple[int, ...]
    evidence: str = ''

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> 'CreatorMnsMaterial':
        return cls(
            tier=str(value['tier']),
            device_tag=str(value['deviceTag']),
            env_const=int(value['envConst']),
            env_fp_tail=_tail_bytes(
                value.get('envFpTailHex', value.get('envFpTail'))
            ),
            evidence=str(value.get('evidence') or ''),
        )


def _reference_mns_stages() -> Dict[str, CreatorMnsMaterial]:
    return {
        name: CreatorMnsMaterial.from_mapping(value)
        for name, value in REFERENCE_PROFILE['mnsStages'].items()
    }


def _reference_mns_profiles() -> Dict[str, CreatorMnsMaterial]:
    return {
        name: CreatorMnsMaterial.from_mapping(value)
        for name, value in REFERENCE_PROFILE.get('mnsProfiles', {}).items()
    }


@dataclass
class CreatorB1RuntimeState:
    """Explicit 19-field Creator b1 collector state.

    Defaults are a browser-derived low-interaction Windows profile.  A captured
    field map can be supplied through ``overrides`` for byte-exact replay.
    """

    frame_count: int
    x39_value: int
    x50_value: str
    x51_value: str
    generated_at_offset_ms: Optional[int]
    sec_canvas: str
    x37_value: str
    x38_value: str
    selected_global_names: list[str] = field(default_factory=list)
    time_origin_ms: float = 0.0
    mouse: Dict[str, Any] = field(default_factory=dict)
    keyboard: Dict[str, Any] = field(default_factory=dict)
    page: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)
    overrides: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def reference(
        cls,
        started_at: Optional[int] = None,
        profile_name: str = 'login',
    ) -> 'CreatorB1RuntimeState':
        """Build a named, browser-derived page profile.

        Creator b1 is a page/runtime snapshot. Login and note-manager pages
        share the algorithm but not every collector field.
        """
        value = dict(REFERENCE_PROFILE['b1Reference'])
        if profile_name not in {'', 'login', 'default'}:
            try:
                value.update(REFERENCE_PROFILE['b1Profiles'][profile_name])
            except KeyError as exc:
                available = ', '.join(
                    ['login', *sorted(REFERENCE_PROFILE.get('b1Profiles', {}))]
                )
                raise ValueError(
                    f'unknown Creator b1 profile {profile_name!r}; '
                    f'available: {available}'
                ) from exc
        origin_base = float(started_at if started_at is not None else now_ms())
        state = cls(
            frame_count=int(value['frameCount']),
            x39_value=int(value['x39']),
            x50_value=str(value['x50']),
            x51_value=str(value.get('x51') or ''),
            generated_at_offset_ms=(
                int(value['generatedAtOffsetMs'])
                if value.get('generatedAtOffsetMs') is not None
                else None
            ),
            sec_canvas=str(value['secCanvas']),
            x37_value=str(value['x37']),
            x38_value=str(value['x38']),
            selected_global_names=list(value['selectedGlobalNames']),
            time_origin_ms=origin_base + float(value.get('timeOriginOffsetMs') or 0),
            mouse=dict(value.get('mouse') or {}),
            keyboard=dict(value.get('keyboard') or {}),
            page=dict(value.get('page') or {}),
            state=dict(value.get('state') or {}),
            features=dict(value.get('features') or {}),
        )
        # A caller-supplied start time denotes a captured fixture and must
        # remain byte-for-byte reproducible.  Live sessions (no explicit
        # start time) still receive the per-session collector variation that
        # the browser emits.
        if started_at is None:
            state._jitter(origin_base)
        return state

    def _jitter(self, origin_base: float) -> None:
        """Decluster per-session b1 fields (2026-07-25 evidence).

        A static fixture b1 reused across fresh devices is cluster-flagged by
        the edge (qr-code/verify-code HTTP 406); jittering these fields per
        session passes immediately.  Only fields a real browser varies across
        sessions are touched; build-constant fields (x38/x42/x43/x45/x50/x82)
        stay at their fixture values.
        """
        import random

        # frameCount: login fixture 2 / note-manager 6; real pages vary ±1
        self.frame_count = max(1, self.frame_count + random.choice((-1, 0, 1)))
        # x37 is a stable capability bitset for the current Chrome 152
        # Creator collector; keep the captured publish-page pattern intact.
        # Creator 4.3.6 currently reports a 16-22 collector cache count on
        # the publish page (fresh captures: 16, 17, 18, 19).  Values near
        # zero are an old login-page profile and are edge-clustered when
        # reused for authenticated media requests.
        self.x39_value = random.randint(16, 22)
        # timeOrigin: fixture constant -> 50-3000ms before page load
        # Chrome serializes the timing origin with one decimal place.
        self.time_origin_ms = round(origin_base - random.uniform(50, 3000), 1)
        # x84 page telemetry key order matches the 1.19.3 browser serialization
        preference = ('ulr', 'f', 'rs', 'ps')
        self.page = {
            **{key: self.page[key] for key in preference if key in self.page},
            **{key: value for key, value in self.page.items() if key not in preference},
        }

    def telemetry(self) -> str:
        features = {
            'ae': None, 'ak': None, 'cdr': None, 'bf': None, 'fi': None,
            **self.features,
        }
        bf = features['bf']
        bf_text = 'null' if bf is None else (
            f"{{ar:{_js_atom(bf.get('ar'))},fr:{_js_atom(bf.get('fr'))}}}"
        )
        to_text = _js_atom(self.time_origin_ms)
        return (
            f'{{mt:{{to:{to_text}}},'
            f'm:{{{_map_text(self.mouse)}}},'
            f'k:{{{_map_text(self.keyboard)}}},'
            f'p:{{{_map_text(self.page)}}},'
            f'st:{{{_map_text(self.state)}}},'
            f"ft:{{ae:{_js_atom(features['ae'])},ak:{_js_atom(features['ak'])},"
            f"cdr:{_js_atom(features['cdr'])},bf:{bf_text},fi:{_js_atom(features['fi'])}}}}}"
        )

    def to_b1_options(self, timestamp_ms: int) -> Dict[str, Any]:
        overrides = {
            'x36': str(self.frame_count),
            'x37': self.x37_value,
            'x38': self.x38_value,
            # The browser collector truncates the global-name snapshot to
            # 300 characters before encrypting it.
            'x82': '|'.join(self.selected_global_names)[:300],
            'x84': self.telemetry(),
            **self.overrides,
        }
        return {
            'now': int(timestamp_ms),
            'x39': int(self.x39_value),
            'x50': str(self.x50_value),
            'x51': str(self.x51_value),
            'secCanvas': str(self.sec_canvas),
            'overrides': overrides,
        }

    def update_window_state(
        self,
        *,
        frame_count: Optional[int] = None,
        x39_value: Optional[int] = None,
        x50_value: Optional[str] = None,
        x51_value: Optional[str] = None,
        sec_canvas: Optional[str] = None,
        selected_global_names: Optional[Iterable[str]] = None,
    ) -> None:
        if frame_count is not None:
            self.frame_count = int(frame_count)
        if x39_value is not None:
            self.x39_value = int(x39_value)
        if x50_value is not None:
            self.x50_value = str(x50_value)
        if x51_value is not None:
            self.x51_value = str(x51_value)
        if sec_canvas is not None:
            self.sec_canvas = str(sec_canvas)
        if selected_global_names is not None:
            self.selected_global_names = [str(item) for item in selected_global_names]


@dataclass
class CreatorSessionState:
    loadts: int
    dsllt: int
    ets: int
    mns_seq: int = 0
    security_ready: bool = False
    profile_count: int = 0
    sign_count: int = 0

    def next_seq(self) -> int:
        self.mns_seq += 1
        return self.mns_seq

    def ensure_dsllt(self, timestamp_ms: int, force: bool = False) -> int:
        timestamp = int(timestamp_ms)
        if force or timestamp - int(self.dsllt) >= DS_REFRESH_INTERVAL_MS:
            self.dsllt = timestamp
        return int(self.dsllt)

    def snapshot(self) -> Dict[str, Any]:
        return {
            'loadts': int(self.loadts),
            'dsllt': int(self.dsllt),
            'ets': int(self.ets),
            'mnsSeq': int(self.mns_seq),
            'securityReady': bool(self.security_ready),
            'p1': int(self.profile_count),
            'sc': int(self.sign_count),
        }


@dataclass
class CreatorDeviceProfile:
    """Creator b1/MNS/X-S-Common/profileData state without browser dependencies."""

    cookies: Any = ''
    local_storage: Mapping[str, Any] = field(default_factory=dict)
    session_storage: Mapping[str, Any] = field(default_factory=dict)
    fixed_b1: str = ''
    dsl: str = ''
    ds_program: str = field(default='', repr=False)
    release: Dict[str, Any] = field(
        default_factory=lambda: dict(REFERENCE_PROFILE['release'])
    )
    b1_state: Optional[CreatorB1RuntimeState] = None
    session: Optional[CreatorSessionState] = None
    mns_stages: Dict[str, CreatorMnsMaterial] = field(
        default_factory=_reference_mns_stages
    )
    mns_profiles: Dict[str, CreatorMnsMaterial] = field(
        default_factory=_reference_mns_profiles
    )
    web_profile_fields: Dict[str, Any] = field(default_factory=dict)
    source: str = 'reference'
    _cookie_map: Dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _named_b1_states: Dict[str, CreatorB1RuntimeState] = field(
        default_factory=dict, init=False, repr=False
    )
    _named_b1_values: Dict[str, str] = field(
        default_factory=dict, init=False, repr=False
    )
    _b1_state_explicit: bool = field(default=False, init=False, repr=False)
    _mns_stage_overrides: set[str] = field(
        default_factory=set, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._cookie_map = parse_cookie_kv(self.cookies)
        local = {str(k): v for k, v in dict(self.local_storage or {}).items()}
        tab = {str(k): v for k, v in dict(self.session_storage or {}).items()}
        started = int(self._cookie_map.get('loadts') or now_ms())
        if self.session is None:
            self.session = CreatorSessionState(
                loadts=started,
                dsllt=int(local.get('dsllt') or started),
                ets=int(self._cookie_map.get('ets') or started),
                mns_seq=int(local.get('mns_seq') or 0),
                security_ready=bool(
                    self._cookie_map.get('websectiga')
                    or self._cookie_map.get('gid')
                    or self.dsl
                ),
                profile_count=int(local.get('p1') or 0),
                sign_count=int(tab.get('sc') or local.get('sc') or 0),
            )
        self._b1_state_explicit = self.b1_state is not None
        if self.b1_state is None:
            self.b1_state = CreatorB1RuntimeState.reference(started_at=started)
        self.web_profile_fields = {
            str(key): value for key, value in dict(self.web_profile_fields or {}).items()
        }

    @property
    def cookie_map(self) -> Dict[str, str]:
        return dict(self._cookie_map)

    @property
    def document_cookie(self) -> str:
        return document_cookie_header(self._cookie_map)

    def update_cookies(self, cookies: Any) -> None:
        updates = parse_cookie_kv(cookies)
        self._cookie_map.update(updates)
        self.cookies = cookie_header(self._cookie_map)
        if updates.get('loadts'):
            self.session.loadts = int(updates['loadts'])
        if updates.get('ets'):
            self.session.ets = int(updates['ets'])
        if updates.get('websectiga') or updates.get('gid'):
            self.session.security_ready = True

    def activate_security(
        self,
        dsl: str,
        ds_program: str = '',
        *,
        timestamp_ms: Optional[int] = None,
    ) -> None:
        self.dsl = str(dsl or '')
        if ds_program:
            self.ds_program = str(ds_program)
        # Creator sets dsllt when the DS program is installed, before the
        # first mns0101 request. It is not lazily created by redcaptcha/CAS.
        self.session.dsllt = int(
            timestamp_ms if timestamp_ms is not None else now_ms()
        )
        self.session.security_ready = True

    def resolve_mns_tier(self, explicit_tier: Optional[str] = None) -> str:
        if explicit_tier is not None:
            tier = str(explicit_tier)
            if tier not in {'0101', '0201'}:
                raise ValueError(f'unsupported Creator MNS tier: {tier}')
            return tier
        return '0101' if self.session.security_ready else '0201'

    def resolve_mns_material(
        self,
        *,
        tier: Optional[str] = None,
        mns_profile: Optional[str] = None,
    ) -> tuple[str, CreatorMnsMaterial]:
        """Resolve the exact MNS tier/material without advancing sequence state."""
        resolved = self.resolve_mns_tier(tier)
        stage_key = 'bootstrap' if resolved == '0201' else 'ready'
        material = self.mns_stages[stage_key]
        if mns_profile and stage_key not in self._mns_stage_overrides:
            try:
                candidate = self.mns_profiles[str(mns_profile)]
            except KeyError as exc:
                available = ', '.join(sorted(self.mns_profiles)) or '(none)'
                raise ValueError(
                    f'unknown Creator MNS profile {mns_profile!r}; '
                    f'available: {available}'
                ) from exc
            if candidate.tier != resolved:
                raise ValueError(
                    f'Creator MNS profile {mns_profile!r} uses '
                    f'{candidate.tier}, request resolved to {resolved}'
                )
            material = candidate
        # The current Creator page uses route-specific ready-tier environment
        # constants.  A fresh publish tab observed 1337 for the first
        # user/info call, 1341 for mountable APIs, 1349 for upload permits,
        # and 1350 for webprofile/security refreshes.  These are not
        # image/video constants, so both permit scenes share 1349.
        if (
            resolved == '0101'
            and stage_key not in self._mns_stage_overrides
            and str(mns_profile or '') not in {'login_early', 'login_callback'}
        ):
            profile_key = str(mns_profile or '')
            if profile_key == 'publish_user_info':
                env_const = 1337
            elif profile_key == 'publish_mountable':
                env_const = 1341
            elif profile_key in {
                'publish_permit', 'publish_permit_image',
                'publish_permit_video',
            }:
                env_const = 1349
            elif profile_key in {'note_manager', 'note_manager_steady'}:
                # These profiles already carry their own captured route
                # constant (currently 1339).  They predate the publish-page
                # route table and must not be rewritten to the generic 1351
                # fallback below.
                env_const = int(material.env_const)
            elif profile_key == 'login_ready':
                env_const = 1350
            else:
                env_const = 1351
            if int(material.env_const) != env_const:
                material = CreatorMnsMaterial(
                    tier=material.tier,
                    device_tag=material.device_tag,
                    env_const=env_const,
                    env_fp_tail=material.env_fp_tail,
                    evidence=(
                        f'{material.evidence}; route profile={profile_key or "default"}'
                    ),
                )
        return resolved, material

    def set_mns_stage(
        self,
        name_or_tier: str,
        *,
        env_const: int,
        env_fp_tail: Any,
        device_tag: Optional[str] = None,
        evidence: str = 'runtime override',
    ) -> None:
        key = 'bootstrap' if str(name_or_tier) == '0201' else 'ready'
        current = self.mns_stages[key]
        self.mns_stages[key] = CreatorMnsMaterial(
            tier=current.tier,
            device_tag=str(device_tag or current.device_tag),
            env_const=int(env_const),
            env_fp_tail=_tail_bytes(env_fp_tail),
            evidence=str(evidence),
        )
        self._mns_stage_overrides.add(key)

    def next_sign_context(
        self,
        *,
        tier: Optional[str] = None,
        mns_profile: Optional[str] = None,
        timestamp_ms: Optional[int] = None,
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        import secrets

        resolved, material = self.resolve_mns_material(
            tier=tier,
            mns_profile=mns_profile,
        )
        timestamp = int(timestamp_ms if timestamp_ms is not None else now_ms())
        return {
            'tier': resolved,
            'now': timestamp,
            'version': int(version if version is not None else secrets.randbits(32)),
            'loadts': int(self.session.loadts),
            'seq': int(self.session.next_seq()),
            'envConst': int(material.env_const),
            'envFpTail': list(material.env_fp_tail),
            'deviceTag': material.device_tag,
            'b1b1': str(self.local_storage.get('b1b1') or '1'),
            'signCount': int(self.session.sign_count),
            'webBuild': str(self.release['webBuild']),
            'signVersion': str(self.release['signVersion']),
            'appId': str(self.release['appId']),
            'platform': str(self.release['platform']),
            'userAgent': str(self.release['userAgent']),
            'secChUa': str(self.release['secChUa']),
            'dsProgram': str(self.ds_program or ''),
        }

    def current_b1(
        self,
        timestamp_ms: Optional[int] = None,
        profile_name: Optional[str] = None,
    ) -> str:
        if self.fixed_b1:
            return self.fixed_b1
        from .runtime import generate_b1

        timestamp = int(timestamp_ms if timestamp_ms is not None else now_ms())
        state = self.b1_state
        if profile_name and not self._b1_state_explicit:
            key = str(profile_name)
            cached = self._named_b1_values.get(key)
            if cached:
                return cached
            state = self._named_b1_states.get(key)
            if state is None:
                state = CreatorB1RuntimeState.reference(
                    started_at=self.session.loadts,
                    profile_name=key,
                )
                self._named_b1_states[key] = state
            generated_at = timestamp
            if state.generated_at_offset_ms is not None:
                generated_at = int(
                    self.session.loadts + state.generated_at_offset_ms
                )
            value = generate_b1(state.to_b1_options(generated_at))
            self._named_b1_values[key] = value
            return value
        return generate_b1(state.to_b1_options(timestamp))

    def dsl_pair(self, timestamp_ms: Optional[int] = None) -> str:
        timestamp = int(timestamp_ms if timestamp_ms is not None else now_ms())
        dsllt = self.session.ensure_dsllt(timestamp)
        return f'{dsllt};{self.dsl or "undefined"}'

    def profile_data_options(
        self,
        *,
        timestamp_ms: Optional[int] = None,
        location: str = 'https://creator.xiaohongshu.com/login',
        referer: str = 'https://creator.xiaohongshu.com/login',
    ) -> Dict[str, Any]:
        timestamp = int(timestamp_ms if timestamp_ms is not None else now_ms())
        return {
            'timestampMs': timestamp,
            'timeOrigin': float(self.b1_state.time_origin_ms),
            'documentCookie': self.document_cookie,
            'location': location,
            'referer': referer,
            'fields': dict(self.web_profile_fields),
        }

    def state_snapshot(self) -> Dict[str, Any]:
        state = self.session.snapshot()
        state.update({
            'webBuild': self.release['webBuild'],
            'xsecappid': self.release['appId'],
            'deviceTag': (
                self.mns_stages['ready'].device_tag
                if self.session.security_ready
                else self.mns_stages['bootstrap'].device_tag
            ),
        })
        return state


__all__ = [
    'REFERENCE_PROFILE',
    'DS_REFRESH_INTERVAL_MS',
    'CreatorMnsMaterial',
    'CreatorB1RuntimeState',
    'CreatorSessionState',
    'CreatorDeviceProfile',
    'parse_cookie_kv',
    'cookie_header',
    'document_cookie_header',
    'now_ms',
]
