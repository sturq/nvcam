#extension GL_OES_EGL_image_external : require
#extension GL_OES_standard_derivatives : enable
precision highp float;

varying vec2 vTexCoord;
uniform samplerExternalOES sTexture;
uniform vec2 uResolution;
uniform float uTime;

// constants kept in sync with tools/nv_sim.py
// Camcorder night-shot look, matched to sturq's reference frame: almost monochrome, blacks
// near black with a faint purple, neutral mids, mint-white highlights that glow, soft detail,
// light grain, slight barrel bulge and vignette. Deliberately subtle: no tube edge, no
// scanlines, no reticle.
const float BARREL = 0.05;           // lens bulge, 0 = flat
const float SOFT = 0.0018;           // blur tap spacing, fraction of the short side
const float GAIN = 1.10;             // exposure push before the curve
const float GAMMA = 1.10;            // >1 keeps the darks dark
const float BLACK_LIFT = 0.03;       // reference blacks sit around 12/255
const float HALO_THRESHOLD = 0.75;
const float HALO_RADIUS = 0.02;      // fraction of the short side
const float HALO_STRENGTH = 0.45;
const float GRAIN_AMP = 0.06;
const float VIGNETTE_STRENGTH = 0.45;
const vec3  SHADOW_TINT = vec3(1.10, 0.90, 1.12);     // luma-neutral faint purple
const vec3  HIGHLIGHT_TINT = vec3(0.94, 1.03, 0.98);  // luma-neutral mint
const float WHITE_ROLLOFF = 0.5;     // how far the brightest parts bleach toward white

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float tap(vec2 uv) { return luma(texture2D(sTexture, uv).rgb); }

void main() {
    // One screen pixel in texture space. The texture can be rotated against the output,
    // so pixel offsets go through the derivatives instead of 1/uResolution.
    vec2 ex = dFdx(vTexCoord);
    vec2 ey = dFdy(vTexCoord);
    float shortSide = min(uResolution.x, uResolution.y);

    // Barrel bulge, circular on screen, corners stay put.
    vec2 s = (gl_FragCoord.xy - 0.5 * uResolution) / uResolution.y;
    float rc2 = 0.25 * (uResolution.x / uResolution.y) * (uResolution.x / uResolution.y) + 0.25;
    float k = (1.0 + BARREL * dot(s, s)) / (1.0 + BARREL * rc2);
    vec2 uv = 0.5 + (vTexCoord - 0.5) * k;

    // 3x3 gaussian (1 2 1 / 2 4 2 / 1 2 1), taps under 2 px apart so edges blur instead of doubling
    vec2 a = ex * SOFT * shortSide;
    vec2 b = ey * SOFT * shortSide;
    float l = (4.0 * tap(uv)
            + 2.0 * (tap(uv + a) + tap(uv - a) + tap(uv + b) + tap(uv - b))
            + tap(uv + a + b) + tap(uv + a - b) + tap(uv - a + b) + tap(uv - a - b)) / 16.0;

    float hr = HALO_RADIUS * shortSide;
    float halo = 0.0;
    for (int i = 0; i < 8; i++) {
        float ang = float(i) * 0.785398;
        vec2 d = ex * cos(ang) + ey * sin(ang);
        halo += 0.5 * smoothstep(HALO_THRESHOLD, 1.0, tap(uv + d * hr));
        halo += smoothstep(HALO_THRESHOLD, 1.0, tap(uv + d * hr * 0.5));
    }
    l += halo / 12.0 * HALO_STRENGTH;

    l = pow(clamp(l * GAIN, 0.0, 1.0), GAMMA);
    l += (hash(floor(uv * uResolution * 0.5) + uTime) - 0.5) * GRAIN_AMP * (1.0 - 0.5 * l);
    l = clamp(BLACK_LIFT + (1.0 - BLACK_LIFT) * l, 0.0, 1.0);

    vec3 col = l * mix(SHADOW_TINT, HIGHLIGHT_TINT, smoothstep(0.05, 0.35, l));
    col = mix(col, vec3(1.0), smoothstep(0.85, 1.0, l) * WHITE_ROLLOFF);

    vec2 q = vTexCoord - 0.5;
    col *= 1.0 - dot(q, q) * VIGNETTE_STRENGTH;

    gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
