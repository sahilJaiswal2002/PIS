# Design Guidelines for IITB Medical Patient Data Collection System

## Design Approach

**Selected System:** Material Design 3 with healthcare adaptations
**Rationale:** Medical applications demand clarity, accessibility, and trust. Material Design provides robust components for data-heavy interfaces while maintaining professional aesthetics suitable for healthcare contexts.

**Key Design Principles:**
1. **Clarity First:** Every interface element serves a clear purpose with no ambiguity
2. **Progressive Disclosure:** Complex information revealed step-by-step to reduce cognitive load
3. **Trustworthy Professionalism:** Design conveys competence and security for medical data handling
4. **Accessibility Priority:** WCAG AA compliance minimum for all interactive elements

## Typography System

**Font Family:** 
- Primary: Inter (via Google Fonts) - exceptional readability for forms and data
- Monospace: JetBrains Mono - for IDs, reference numbers, timestamps

**Type Scale:**
- Hero/Page Titles: text-4xl font-bold (36px)
- Section Headers: text-2xl font-semibold (24px)
- Subsection Headers: text-xl font-medium (20px)
- Body Text: text-base font-normal (16px)
- Form Labels: text-sm font-medium (14px)
- Helper Text/Captions: text-sm font-normal (14px)
- Data Tables: text-sm font-normal (14px)

## Layout System

**Spacing Primitives:** Tailwind units of 2, 4, 6, 8, and 12 (e.g., p-4, m-8, gap-6)
- Tight spacing: 2-4 units for related elements
- Standard spacing: 6-8 units for component separation
- Section spacing: 12-16 units for major divisions

**Container Strategy:**
- Admin Dashboard: Full-width with max-w-7xl centered container
- Patient Forms: max-w-3xl centered for optimal reading width
- Data Tables: Full-width responsive containers with horizontal scroll

**Grid Patterns:**
- Admin Cards Grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6
- Form Layout: Single column with logical grouping
- Dashboard Stats: grid-cols-2 lg:grid-cols-4 for metrics

## Component Library

### Navigation & Layout

**Admin Sidebar:**
- Fixed left sidebar (w-64) on desktop, collapsible on mobile
- Logo/branding at top with institution badge
- Grouped navigation items with icons (Dashboard, Diseases, Hospitals, Doctors, Forms, Submissions)
- Active state with subtle indicator and type weight change
- User profile section at bottom with role badge

**Patient Header:**
- Horizontal navigation with IITB branding left-aligned
- Progress stepper (Disease → Hospital → Doctor → Form) center-aligned on desktop
- User menu right-aligned with logout option
- Sticky positioning for form pages

**Breadcrumbs:**
- Present on all pages for orientation
- Positioned below header with separator icons
- Last item non-clickable and emphasized

### Admin Components

**Management Tables:**
- Zebra striping for row distinction
- Sortable column headers with sort indicators
- Action column (right-aligned) with icon buttons (Edit, Delete, View)
- Search bar above table with filter chips
- Pagination at bottom (10/25/50 items per page options)
- Empty states with illustrative messaging and CTA

**Form Builder Interface:**
- Left panel: Field palette with drag indicators (Text Input, Textarea, Dropdown, Radio, Checkbox, Date, File Upload, Number)
- Center canvas: Live form preview with field reordering
- Right panel: Field properties (label, placeholder, required toggle, validation rules)
- Top toolbar: Form title, save/publish buttons, preview toggle

**CRUD Modals:**
- Centered overlay with backdrop blur
- Clear title with close button
- Form fields with consistent spacing (gap-4)
- Actions aligned right (Cancel, Save/Create)
- Maximum width max-w-2xl

### Patient-Facing Components

**Step Selection Cards:**
- Large clickable cards (min-h-32) with icon, title, description
- Hover state with subtle elevation change
- Selected state with checkmark indicator
- Disabled state for unavailable options with explanation tooltip
- Grid layout adapting to screen size

**Form Components:**
- Clear field labels positioned above inputs
- Required field indicators with asterisk
- Helper text below fields in smaller, muted type
- Error states with inline validation messaging
- Field grouping with subtle dividers
- File upload with drag-and-drop zone and preview
- Section headers for logical form divisions

**Progress Stepper:**
- Horizontal stepper showing 4 steps
- Completed steps with checkmarks
- Current step highlighted with prominent indicator
- Future steps in muted state
- Step labels beneath indicators
- Connecting lines between steps

### Data Display

**Dashboard Cards:**
- Elevated cards with rounded corners
- Icon or illustration in accent area
- Metric number prominently displayed (text-3xl font-bold)
- Label and trend indicator below
- Consistent padding (p-6)

**Status Badges:**
- Rounded full badges for states (Pending, Reviewed, Approved, Rejected)
- Sizes: Small (px-2.5 py-0.5 text-xs), Medium (px-3 py-1 text-sm)
- Icon + text combination when needed

**Data Lists:**
- Alternating background for readability
- Clear labels with data in consistent alignment
- Responsive stacking on mobile
- Expandable rows for detailed information

### Forms & Inputs

**Input Fields:**
- Consistent height (h-11 for text inputs)
- Rounded corners (rounded-md)
- Full-width within containers
- Border with focus state indicator
- Disabled state with reduced opacity

**Buttons:**
- Primary: Solid fill for main actions (h-11 px-6 rounded-md font-medium)
- Secondary: Outline style for secondary actions
- Text: No background for tertiary actions
- Icon buttons: Square (h-10 w-10) for table actions
- Loading states with spinner
- Full-width on mobile for primary CTAs

**Form Sections:**
- Visual separation with borders or spacing
- Collapsible sections for lengthy forms
- Summary view before submission

### Feedback & States

**Loading States:**
- Skeleton screens for table/card loading
- Spinner overlays for form submissions
- Progress indicators for multi-step processes

**Empty States:**
- Centered with illustrative icon
- Clear message explaining the empty state
- Primary CTA to add first item
- Helpful suggestions where appropriate

**Success/Error Messages:**
- Toast notifications (top-right position)
- Auto-dismiss after 5 seconds with manual close option
- Icon + message + action (if applicable)
- Inline errors below form fields with icon

**Confirmation Dialogs:**
- Centered modal with critical action warning
- Clear description of consequences
- Destructive action in accent style
- Cancel emphasized over destructive action

## Animations

**Minimal & Purposeful:**
- Page transitions: Fade in (duration-200)
- Modal/Dialog: Scale + fade (duration-300)
- Dropdown menus: Slide down (duration-200)
- Form validation: Shake on error (duration-300)
- NO scroll-triggered animations
- NO complex hover animations beyond subtle opacity/shadow changes

## Images

**Landing/Login Page:**
- Hero Image: Professional medical/healthcare imagery showing diversity and technology
- Placement: Left half of split screen (hidden on mobile)
- Treatment: Subtle overlay gradient for text readability
- Alternative: IITB campus with medical facility focus

**Dashboard:**
- Empty state illustrations: Custom line-art style illustrations for empty tables/lists
- Profile avatars: Circular with fallback to initials

**No hero image required** for internal admin/patient form pages - focus on functional clarity.

## Responsive Behavior

**Breakpoints:**
- Mobile: Base (< 768px) - Single column, stacked navigation
- Tablet: md (768px+) - Two columns where appropriate, condensed sidebar
- Desktop: lg (1024px+) - Full layout with sidebar, multi-column grids

**Mobile Specific:**
- Bottom navigation for primary actions on forms
- Hamburger menu for admin sidebar
- Stepper becomes vertical or simplified dots
- Tables switch to card view with key information
- Forms maintain single column with full-width inputs

## Accessibility Implementation

**Mandatory Elements:**
- All interactive elements keyboard accessible
- Focus indicators on all focusable elements (ring-2)
- ARIA labels for icon-only buttons
- Form fields with associated labels (not placeholder-only)
- Color contrast minimum 4.5:1 for text
- Screen reader announcements for dynamic content changes
- Error messages programmatically associated with fields