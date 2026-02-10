# Style Description

## Coding Style

The frontend is built with React and TypeScript, emphasizing modern, functional programming practices for maintainability and type safety.

### Key Principles

- **Functional Components**: Use functional components with hooks (useState, useEffect, useCallback) instead of class components.
- **TypeScript Strictness**: Leverage TypeScript for explicit type annotations on props, state, and return types to prevent runtime errors.
- **Modular Architecture**: Organize code into logical modules: components, services, types, constants, and hooks. Services handle API interactions, components manage UI, and types define data structures.
- **Async/Await**: Use async/await for asynchronous operations like API calls, with proper error handling using try/catch blocks.
- **State Management**: Manage component state with useState hooks; avoid complex state libraries unless necessary.
- **Responsive Design**: Implement responsive layouts using Tailwind CSS utilities, with mobile-first approach.
- **Styling**: Use Tailwind CSS for utility-first styling, adhering to the brutalist/comic book theme with custom classes and transforms.
- **Error Handling**: Provide user-friendly error messages and handle API errors gracefully.
- **Comments**: Add comments for complex logic, multi-step processes, and non-obvious code sections.
- **Imports**: Group imports by type (React, types, services, components) and keep them at the top of files.
- **Naming Conventions**: Use PascalCase for components, camelCase for variables/functions, and descriptive names that reflect the brutalist theme where appropriate (e.g., error messages in uppercase).
- **Performance**: Use useCallback for event handlers to prevent unnecessary re-renders, and optimize images with responsive srcsets.

## Mascot

The website has a mascot named Wata Bautet. He is designed in the style of brutalist 80s anime and British Underground Comix.

## Composition and Background

The website should look like a comic book page with elements of a hacked terminal screen.

Background: White, but not sterile. It has the texture of thick comic book paper, with a slight grain, perhaps with small blobs of black ink or typographic "noise" (halftone dots) in the corners.

Drawing Style: Bold black outlines, sharp shadows, limited palette (black, white, electric yellow, violet-blue).

## UI Elements (Interface)

The interface doesn't "float"; it's integrated into the comic book world.

Link Input Field: It's not just a rectangle. It could be stylized as a crack in space or a roughly outlined block with handwritten text on the background: "URL SOURCE." The font looks like it was scrawled with a marker.

Resume size selection: Not a standard select or radio button. It's a slider-lever (like on an old audio amplifier).

Gradation: The labels are "Essense" - "Thesis" - "Longread."

Action button: The most striking element. It's not rectangular and boring. It's a jagged "explosion" (like in comics when you hit someone) with the text "EXTRACT." It's yellow with black cracks/lightning bolts.

## Typography

Headings: Aggressive lettering, reminiscent of punk band logos or Judge Dredd titles.

Main text: A monospaced font (like the ones found in old DOS terminals) symbolizes erudition and technology.

Rebel minimalism: Nothing superfluous, just a field, a setting, and a button, yet it all looks stylish and "loud."
