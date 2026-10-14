# UniWay React Aria school picker

This React island enhances the school-switching dialog with React Aria Components
`ModalOverlay`, `Modal`, `Dialog`, `Autocomplete`, `SearchField`, `ListBox` and
`Button`, styled with plain CSS and the existing UniWay glass tokens.

The native app supplies supported schools, aliases, the current school and its
existing selection/dismissal callbacks through `window.UniWaySchoolPicker`.
React owns the dialog DOM, filtering and accessibility. Account requests,
school-specific workspaces, shared links and catalogue loads stay in `app.js`.
Results activate on a click or Enter; arrow navigation does not change the school.
Cancelling preserves an existing selection. New visitors can dismiss the dialog
and continue browsing public data. Account saves disable further choices and
dismissal until the request finishes. Saving times out after 20 seconds, unlocks
the UI and asks the student to reload to confirm whether the account was updated.

The overlay portals into the original school picker host. React Aria handles
focus containment, hiding the background from assistive technology and scroll
locking. The host keeps its existing ID for navigation, loading and motion hooks.
The original HTML and native listeners remain a fallback when the bundle cannot
load. All scripts, styles and licenses are served locally under the existing CSP.

## Build

With Node.js 20 or newer, from this directory:

```sh
npm ci
npm run build
```

Commit source and lockfile changes together with the generated
`src/exchange_info/static/react-aria-school-picker.js`, `.css` and `.js.LEGAL.txt`.
Python packaging already includes these files. Serving the site requires no
additional Node process. CI rebuilds the bundle to verify the committed output.

Official references: [Modal](https://react-aria.adobe.com/Modal),
[Autocomplete](https://react-aria.adobe.com/Autocomplete),
[ListBox](https://react-aria.adobe.com/ListBox), and
[SearchField](https://react-aria.adobe.com/SearchField).
