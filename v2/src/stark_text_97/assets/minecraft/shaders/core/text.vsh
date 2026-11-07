#version 330
#extension GL_ARB_separate_shader_objects : require

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
#include <minecraft:fog.glsl>
#include <minecraft:sample_lightmap.glsl>
#endif

#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <minecraft:globals.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
layout(location = 3) in ivec2 UV2;
#endif

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
uniform sampler2D Sampler2;
layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
#endif

layout(location = 2) out vec4 vertexColor;
layout(location = 3) out vec2 texCoord0;

// ---- STARK FFA name styles (pack r40, StarkCore cosmetics/NameStyle) ----
// Animated text is sent in EXACT marker colours (8 per style, table below = the fallback gradient on clients without
// this shader); its black shadow is rgb(6, 3, 16 + style). Every other colour is drawn exactly as before.
const int STARK_STYLES = 10;
const int STARK_KIND[10] = int[10](0, 1, 2, 3, 4, 5, 6, 7, 0, 0);
const ivec3 STARK_PAL[80] = ivec3[80](
    ivec3(253, 166, 47), ivec3(253, 178, 71), ivec3(253, 190, 91), ivec3(253, 206, 111), ivec3(253, 214, 135), ivec3(253, 222, 155), ivec3(253, 230, 175), ivec3(253, 242, 195),
    ivec3(253, 62, 87), ivec3(253, 78, 103), ivec3(253, 98, 123), ivec3(253, 114, 139), ivec3(253, 130, 155), ivec3(253, 146, 167), ivec3(253, 162, 183), ivec3(253, 178, 199),
    ivec3(45, 106, 255), ivec3(53, 126, 255), ivec3(57, 146, 255), ivec3(61, 166, 255), ivec3(65, 186, 255), ivec3(73, 206, 255), ivec3(85, 222, 255), ivec3(93, 242, 255),
    ivec3(165, 230, 255), ivec3(181, 234, 255), ivec3(193, 238, 255), ivec3(205, 242, 255), ivec3(221, 246, 255), ivec3(233, 250, 255), ivec3(241, 254, 255), ivec3(253, 254, 255),
    ivec3(253, 106, 107), ivec3(253, 150, 107), ivec3(253, 194, 103), ivec3(213, 222, 119), ivec3(149, 242, 143), ivec3(105, 246, 175), ivec3(105, 226, 215), ivec3(105, 202, 255),
    ivec3(233, 54, 31), ivec3(237, 74, 35), ivec3(245, 94, 39), ivec3(253, 114, 43), ivec3(253, 134, 51), ivec3(253, 158, 59), ivec3(253, 178, 75), ivec3(253, 202, 79),
    ivec3(45, 218, 255), ivec3(73, 222, 255), ivec3(101, 230, 255), ivec3(125, 238, 255), ivec3(149, 242, 255), ivec3(173, 246, 255), ivec3(193, 250, 255), ivec3(217, 250, 255),
    ivec3(157, 122, 255), ivec3(169, 138, 255), ivec3(181, 154, 255), ivec3(193, 170, 255), ivec3(205, 182, 255), ivec3(213, 198, 255), ivec3(225, 214, 255), ivec3(237, 226, 255),
    ivec3(173, 186, 203), ivec3(185, 198, 211), ivec3(197, 206, 219), ivec3(209, 218, 227), ivec3(221, 226, 235), ivec3(229, 234, 243), ivec3(237, 242, 247), ivec3(245, 250, 255),
    ivec3(225, 94, 255), ivec3(229, 110, 255), ivec3(237, 130, 255), ivec3(241, 146, 255), ivec3(245, 162, 255), ivec3(249, 182, 255), ivec3(253, 198, 255), ivec3(253, 214, 255)
);

const float STARK_TAU = 6.2831853;

vec3 stark_hsv2rgb(vec3 c) {
    vec3 p = abs(fract(vec3(c.x) + vec3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - vec3(3.0));
    return c.z * mix(vec3(1.0), clamp(p - vec3(1.0), 0.0, 1.0), c.y);
}

vec3 stark_rgb2hsv(vec3 c) {
    vec4 k = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.b, c.g, k.w, k.z), vec4(c.g, c.b, k.x, k.y), step(c.b, c.g));
    vec4 q = mix(vec4(p.x, p.y, p.w, c.r), vec4(c.r, p.y, p.z, p.x), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1.0e-10)), d / (q.x + 1.0e-10), q.x);
}

float stark_hash(float n) {
    return fract(sin(n * 12.9898 + 4.1414) * 43758.5453);
}

// style index (-1 = plain text), letter index 0-7, shadow?
int stark_find(ivec3 c, out int letter, out bool shadow) {
    letter = 0;
    shadow = false;
    if (c.r == 6 && c.g == 3 && c.b >= 16 && c.b < 16 + STARK_STYLES) {
        shadow = true;
        return c.b - 16;
    }
    for (int i = 0; i < STARK_STYLES * 8; i++) {
        if (c == STARK_PAL[i]) {
            letter = i - (i / 8) * 8;
            return i / 8;
        }
    }
    return -1;
}

// x = horizontal position in GUI pixels, corner = 0 top-left, 1 bottom-left, 2 bottom-right, 3 top-right
vec4 stark_color(vec4 color, float x, int corner) {
    ivec3 c = ivec3(color.rgb * 255.0 + vec3(0.5));
    int letter;
    bool shadow;
    int style = stark_find(c, letter, shadow);
    if (style < 0) return color;
    int kind = STARK_KIND[style];
    float t = GameTime * 1200.0;
    vec3 base = color.rgb;
    float seed = float(style * 8 + letter) * 1.618 + 0.37;
    vec3 rgb = base;
    float alpha = 1.0;
    if (kind == 0) {
        // GLINT: a white shine sweeps over the letters
        float d = abs(mod(x - t * 44.0, 110.0) - 55.0);
        rgb = mix(base, vec3(1.0), (1.0 - smoothstep(1.0, 6.5, d)) * 0.9);
    } else if (kind == 1) {
        // HEARTBEAT: a double pulse
        float f = fract(t / 1.15);
        float b = exp(-pow(f * 11.0, 2.0)) + 0.7 * exp(-pow((f - 0.2) * 11.0, 2.0));
        rgb = mix(base * 0.7, mix(base, vec3(1.0), 0.35), clamp(b, 0.0, 1.0));
    } else if (kind == 2) {
        // TIDE: the colours flow along the name
        vec3 h = stark_rgb2hsv(base);
        float w = x * 0.11 - t * 2.4;
        h.x = fract(h.x + 0.055 * sin(w));
        h.z = clamp(h.z * (0.86 + 0.14 * sin(w + 1.3)), 0.0, 1.0);
        rgb = stark_hsv2rgb(h);
    } else if (kind == 3) {
        // FROSTBITE: sparkles on random letters
        float tw = pow(max(0.0, sin(t * 1.7 + stark_hash(seed) * STARK_TAU)), 30.0);
        rgb = mix(base * (0.92 + 0.08 * sin(x * 0.2 - t * 1.4)), vec3(1.0), tw * 0.95);
    } else if (kind == 4) {
        // PRISM: a flowing rainbow
        rgb = stark_hsv2rgb(vec3(fract(x * 0.0125 - t * 0.32), 0.6, 1.0));
    } else if (kind == 5) {
        // BLAZE: flickering fire, hot tips
        float top = (corner == 0 || corner == 3) ? 1.0 : 0.0;
        float fl = 0.5 + 0.5 * sin(t * 9.0 + stark_hash(seed) * 40.0) * sin(t * 13.7 + stark_hash(seed + 7.0) * 25.0);
        float heat = clamp(0.22 + 0.52 * top + 0.36 * (fl - 0.4), 0.0, 1.0);
        vec3 low = mix(vec3(0.62, 0.06, 0.04), vec3(1.0, 0.27, 0.1), smoothstep(0.0, 0.45, heat));
        vec3 high = mix(vec3(1.0, 0.6, 0.16), vec3(1.0, 0.93, 0.55), smoothstep(0.75, 1.0, heat));
        rgb = mix(low, high, smoothstep(0.4, 0.8, heat));
    } else if (kind == 6) {
        // VOLT: electric strobes
        float own = step(0.9, stark_hash(floor(t * 14.0) + seed * 3.17));
        float burst = step(0.965, stark_hash(floor(t * 7.0) + 0.37));
        rgb = mix(base * (0.82 + 0.18 * sin(x * 0.6 - t * 18.0)), vec3(1.0), max(own, burst) * 0.92);
    } else {
        // PHANTOM: fades in and out like a ghost
        float f = 0.5 + 0.5 * sin(x * 0.07 - t * 1.6);
        alpha = mix(0.42, 1.0, smoothstep(0.15, 0.85, f));
        rgb = mix(base, vec3(0.95, 0.92, 1.0), 0.25 * f);
    }
    if (shadow) rgb = base;
    return vec4(rgb, color.a * alpha);
}

// horizontal position in GUI pixels (orthographic GUI projection), screen based for text in the world
float stark_px(vec4 pos) {
    float ndc = pos.x / pos.w;
    if (ProjMat[2][3] == 0.0) return (ndc + 1.0) / ProjMat[0][0];
    return (ndc + 1.0) * 0.5 * ScreenSize.x / max(1.0, floor(ScreenSize.y / 270.0));
}
// ---- end STARK FFA name styles ----

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
    sphericalVertexDistance = fog_spherical_distance(Position);
    cylindricalVertexDistance = fog_cylindrical_distance(Position);
    vertexColor = stark_color(Color, stark_px(gl_Position), gl_VertexIndex % 4) * sample_lightmap(Sampler2, UV2);
#else
    vertexColor = stark_color(Color, stark_px(gl_Position), gl_VertexIndex % 4);
#endif
    texCoord0 = UV0;
}
