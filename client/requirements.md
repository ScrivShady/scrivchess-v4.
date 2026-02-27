## Packages
react-markdown | Renders the AI markdown response with proper formatting
remark-gfm | Adds support for GitHub Flavored Markdown (tables, strikethrough, etc.) to react-markdown
clsx | Utility for constructing className strings conditionally
tailwind-merge | Utility to merge tailwind classes without style conflicts

## Notes
- Enforcing a strict dark mode "premium chess coach" aesthetic.
- The Sidebar component manages both configuration settings and history navigation.
- Image uploads are handled purely client-side, converting to base64 before sending to the backend via POST /api/analyses.
