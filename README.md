# The Parametric VA

A parametric human walks a parametric tower. Torre Agbar is rebuilt in Revit from three mass parameters
(R, H, z0) and 1,260 responsive façade panels; the people are Revit families too, with a body, a brain and
a memory, walked through the office floor by the Pawn engine (social force model).

**Live page:** https://faroshad.github.io/VA_Parametric/

ARCH 653 Project 1 · Farshad Askari · Texas A&M University · Fall 2026

## Files

| Path | What |
|---|---|
| `index.html` | the page: text, the live body and access figures, the memory replay, the raw/AI compare, and the WebGL figure that turns from a body into the tower as you scroll |
| `assets/data/va.js` | Pawn engine output for the page: the floor plan, rooms each body can enter, and three runs of the same person (Visitor 1st and 2nd visit, Staff) with the moment each square, door and room enters memory |
| `assets/video/` | Farshad and X side by side (Revit first-person renders + plan with memory, 24x), Farshad's Cycles first-person video, posters |
| `assets/img/` | full-size images for the lightbox; `sm/` smaller copies on the page; `wipe/` raw/AI pairs at the same size |
| `tools/` | the scripts that made `va.js` and the comparison video with the Pawn engine (run on copies of the Project1_v01 run; they need the Pawn engine, which is not in this repo) |

To view it locally, open `index.html` in a browser, or run `python -m http.server` in this folder and open
http://localhost:8000.

## Credits

Torre Agbar: Ateliers Jean Nouvel, Barcelona, 2005. AI use and references are listed at the end of
the page. LED source images are from Pinterest (links on the page).
