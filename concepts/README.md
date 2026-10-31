# MAC and Element interaction exploration

Open `mac-checkin.html` or `attendance.html` through an HTTP static server. These are new coded explorations of the original flows, not historical production screens. The case study keeps original exports separately.

All eight students and both groups are synthetic. State stays in this browser's localStorage; there are no network requests for attendance and no production account integration. Start with Student 01, select a class and check in. Staff view shares the same records. Select students, review, save, cancel or undo. Student numbers 01–08 are available. Two records are initially signed in.

The MAC mark is an unchanged pixel crop from original `signinAE.gif`, frame 240, rectangle (405, 258, 695, 498). It has not been redrawn or recolored. The original student animation remains in the source archive, but is not displayed on the portfolio. The case study shows only the updated MAC interaction. Its original director-controls crop is replaced by a static recreation in the updated dark style, with sample students. The original crop remains in the source archive. The working attendance demo remains linked separately.

Motion is state-based: class selection, cancellable save, panel entry/exit, confirmation check and updated-row feedback. In-flight operations use a cancellation generation so canceled timers cannot commit afterward. Saves are local and delayed 520 ms to expose the cancellable state; this is not a backend latency claim.

Run `node concepts/state.test.cjs` from the project root for state tests. `capture.html` is only a review harness, not application navigation.
