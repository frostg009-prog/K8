// Grid A* for a 2-layer router (layer 0 = F.Cu, layer 1 = B.Cu). Build: gcc -O2 -shared -fPIC astar.c -o libastar.so
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { int f; int idx; } node;
static node *heap; static int hn, hcap;
static void hpush(int f, int idx) {
    if (hn >= hcap) { hcap = hcap ? hcap * 2 : 1 << 16; heap = realloc(heap, hcap * sizeof(node)); }
    int i = hn++; heap[i].f = f; heap[i].idx = idx;
    while (i > 0) { int p = (i - 1) / 2; if (heap[p].f <= heap[i].f) break; node t = heap[p]; heap[p] = heap[i]; heap[i] = t; i = p; }
}
static node hpop(void) {
    node r = heap[0]; heap[0] = heap[--hn]; int i = 0;
    for (;;) { int l = 2 * i + 1, rr = l + 1, m = i;
        if (l < hn && heap[l].f < heap[m].f) m = l; if (rr < hn && heap[rr].f < heap[m].f) m = rr;
        if (m == i) break; node t = heap[m]; heap[m] = heap[i]; heap[i] = t; i = m; }
    return r;
}
// free: 2*W*H bytes (1 = track centre allowed), viaok: W*H, start/goal: 2*W*H, pen: 2*W*H extra cost (0..255)
// returns number of cells in path (written to out, from goal back to start) or -1
int astar(int W, int H, const uint8_t *fre, const uint8_t *viaok, const uint8_t *start, const uint8_t *goal,
          const uint8_t *pen, int via_cost, int *out, int maxout) {
    int N = W * H, NN = 2 * N;
    int *g = malloc(NN * sizeof(int)); int *par = malloc(NN * sizeof(int)); uint8_t *closed = calloc(NN, 1);
    for (int i = 0; i < NN; i++) { g[i] = 0x3fffffff; par[i] = -1; }
    int gx0 = W, gy0 = H, gx1 = -1, gy1 = -1;
    for (int l = 0; l < 2; l++) for (int i = 0; i < N; i++) if (goal[l * N + i]) {
        int x = i % W, y = i / W; if (x < gx0) gx0 = x; if (x > gx1) gx1 = x; if (y < gy0) gy0 = y; if (y > gy1) gy1 = y; }
    if (gx1 < 0) { free(g); free(par); free(closed); return -1; }
    hn = 0;
#define HEU(x, y) ({ int dx = (x) < gx0 ? gx0 - (x) : ((x) > gx1 ? (x) - gx1 : 0); int dy = (y) < gy0 ? gy0 - (y) : ((y) > gy1 ? (y) - gy1 : 0); \
        int mn = dx < dy ? dx : dy, mx = dx < dy ? dy : dx; 10 * mx + 4 * mn; })
    for (int l = 0; l < 2; l++) for (int i = 0; i < N; i++) if (start[l * N + i]) {
        g[l * N + i] = 0; hpush(HEU(i % W, i / W), l * N + i); }
    static const int dx[8] = {1, -1, 0, 0, 1, 1, -1, -1}, dy[8] = {0, 0, 1, -1, 1, -1, 1, -1}, dc[8] = {10, 10, 10, 10, 14, 14, 14, 14};
    int found = -1;
    while (hn) {
        node nd = hpop(); int c = nd.idx; if (closed[c]) continue; closed[c] = 1;
        if (goal[c]) { found = c; break; }
        int l = c / N, i = c % N, x = i % W, y = i / W;
        for (int k = 0; k < 8; k++) {
            int nx = x + dx[k], ny = y + dy[k]; if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
            int ni = l * N + ny * W + nx; if (closed[ni] || !(fre[ni] || goal[ni])) continue;
            if (k >= 4) { // no corner cutting
                int a = l * N + y * W + nx, b = l * N + ny * W + x;
                if (!(fre[a] || goal[a]) || !(fre[b] || goal[b])) continue; }
            int ng = g[c] + dc[k] + pen[ni];
            if (ng < g[ni]) { g[ni] = ng; par[ni] = c; hpush(ng + HEU(nx, ny), ni); }
        }
        if (viaok[i]) { int ni = (1 - l) * N + i;
            if (!closed[ni] && (fre[ni] || goal[ni])) { int ng = g[c] + via_cost;
                if (ng < g[ni]) { g[ni] = ng; par[ni] = c; hpush(ng + HEU(x, y), ni); } } }
    }
    int n = 0;
    if (found >= 0) { int c = found; while (c >= 0 && n < maxout) { out[n++] = c; c = par[c]; } }
    free(g); free(par); free(closed);
    return found >= 0 ? n : -1;
}
