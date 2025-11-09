# Documentation Rules & Structure

**Last Updated:** October 22, 2025

---

## 📋 Documentation Organization Rules

### **1. Single Source of Truth**
- Each topic should have **ONE primary document**
- No duplicate information across multiple files
- Cross-reference other documents instead of repeating content

### **2. File Naming Convention**
```
docs/
├── README.md                    # Overview & quick links
├── RULES.md                     # This file - documentation guidelines
├── CHANGELOG.md                 # Version history & what's new
├── QUICKSTART.md               # Getting started guide
├── USER_GUIDE.md               # Complete user documentation
├── IMPLEMENTATION_LOG.md       # Development progress & features
├── API_REFERENCE.md            # API endpoints documentation
├── FAQ.md                      # Frequently asked questions
└── ARCHITECTURE.md             # Technical architecture & design
```

### **3. Document Categories**

#### **User Documentation** (For End Users)
- `README.md` - Project overview, installation
- `QUICKSTART.md` - Quick 5-minute setup
- `USER_GUIDE.md` - Complete feature guide
- `FAQ.md` - Common questions

#### **Developer Documentation** (For Developers)
- `IMPLEMENTATION_LOG.md` - Implementation details, features added
- `API_REFERENCE.md` - All API endpoints
- `ARCHITECTURE.md` - System design, code structure
- `RULES.md` - Documentation guidelines

#### **Project Management**
- `CHANGELOG.md` - What's new, version history
- `ROADMAP.md` - Future plans (if needed)

### **4. Content Rules**

#### **README.md Must Include:**
- Project title & description
- Key features (bullet points)
- Quick installation
- Link to QUICKSTART
- Link to USER_GUIDE
- Technology stack
- License

#### **CHANGELOG.md Format:**
```markdown
# Changelog

## [v2.0.0] - 2025-10-22
### Added
- Candlestick chart with pattern overlay
- Pattern recognition system

### Changed
- Dashboard layout (70/30 split)

### Fixed
- Mobile responsiveness

## [v1.0.0] - 2025-10-20
...
```

#### **IMPLEMENTATION_LOG.md Format:**
```markdown
# Implementation Log

## Pattern Recognition System (Oct 22, 2025)
**Status:** ✅ Complete

### What Was Built:
- Feature 1
- Feature 2

### Files Created:
- `src/analysis/patterns.py`

### Files Modified:
- `dashboard.html`

### API Endpoints:
- `GET /api/patterns/all`
```

### **5. Maintenance Rules**

#### **When Adding New Feature:**
1. Update `IMPLEMENTATION_LOG.md` with details
2. Update `CHANGELOG.md` with summary
3. Update `USER_GUIDE.md` if user-facing
4. Update `API_REFERENCE.md` if new endpoints
5. Update `README.md` if major feature

#### **What NOT to Do:**
- ❌ Create multiple "SUMMARY" or "PROGRESS" files
- ❌ Duplicate implementation details
- ❌ Create temporary status files
- ❌ Mix user guide with technical details
- ❌ Create redundant "WHATS_NEW" files (use CHANGELOG)

#### **Cleanup Schedule:**
- **Weekly:** Remove outdated temp files
- **Per Release:** Consolidate progress logs
- **Monthly:** Archive old implementation details

### **6. File Consolidation Map**

#### **Consolidate These:**
```
IMPLEMENTATION → IMPLEMENTATION_LOG.md
├── IMPLEMENTATION_SUMMARY.md
├── IMPLEMENTATION_PROGRESS.md
├── STRATEGY_IMPLEMENTATION_COMPLETE.md
├── UI_INTEGRATION_PROGRESS.md
├── PATTERN_RECOGNITION_IMPLEMENTATION.md
└── CHART_OVERLAY_IMPLEMENTATION.md

WHAT'S NEW → CHANGELOG.md
├── WHATS_NEW.md
├── TODAYS_PROGRESS.md
├── SESSION_SUMMARY.md
└── FIXES_AND_ENHANCEMENTS_COMPLETE.md

USER DOCUMENTATION → USER_GUIDE.md
├── USAGE_GUIDE.md
├── DASHBOARD_GUIDE.md
├── NAVIGATION_GUIDE.md
└── QUICKSTART.md (keep separate - entry point)

PROJECT STATUS → README.md + IMPLEMENTATION_LOG.md
├── CURRENT_STATUS.md
├── PROJECT_SUMMARY.md
└── FINAL_SUMMARY.md

DESIGN DOCS → ARCHITECTURE.md
├── PAGE_DESIGN.md
├── IDEATION_SUMMARY.md
├── SETTINGS_AND_ACCOUNTS_IDEATION.md
└── STRATEGY_FEATURES_SUMMARY.md
```

### **7. Archive Policy**

#### **Files to Archive (Move to `docs/archive/`):**
- Old implementation summaries
- Session notes
- Temporary progress files
- Ideation documents (after implementation)
- Design iterations

#### **Files to Delete:**
- Duplicate summaries
- Empty placeholder files
- Outdated status reports

### **8. External Documents**

#### **Keep in Separate Folder:** `docs/requirements/`
```
requirements/
├── scalping-algo-prd.md
├── xcoin-dashboard-prd.md
├── xcoin-patterns-v5.0.md
├── xcoin-performance-v4.0.md
├── xcoin-glass-v3.0.md
└── xcoin-compact-v2.1.md
```

These are **reference documents** (PRDs), not project documentation.

---

## 📂 Recommended Final Structure

```
scalping-bot/
├── README.md                           # Main entry point
├── docs/
│   ├── RULES.md                       # This file
│   ├── CHANGELOG.md                   # Version history
│   ├── QUICKSTART.md                  # 5-min setup
│   ├── USER_GUIDE.md                  # Complete user guide
│   ├── IMPLEMENTATION_LOG.md          # Dev implementation log
│   ├── API_REFERENCE.md               # API documentation
│   ├── ARCHITECTURE.md                # System architecture
│   ├── FAQ.md                         # Common questions
│   │
│   ├── requirements/                  # PRD & design docs
│   │   ├── scalping-algo-prd.md
│   │   ├── xcoin-patterns-v5.0.md
│   │   └── ...
│   │
│   └── archive/                       # Old docs
│       ├── old-summaries/
│       └── session-notes/
│
├── src/
├── config/
└── ...
```

---

## 🔄 Migration Checklist

When reorganizing:
- [ ] Create consolidated documents
- [ ] Move content from old files
- [ ] Add cross-references
- [ ] Update README links
- [ ] Archive old files
- [ ] Delete duplicates
- [ ] Test all links
- [ ] Update .gitignore if needed

---

## ✍️ Writing Guidelines

### **Style:**
- Use clear, concise language
- Include code examples where relevant
- Use emojis sparingly (headers only)
- Format with proper markdown

### **Structure:**
- Start with brief summary
- Use hierarchical headers (##, ###)
- Include table of contents for long docs
- End with "Next Steps" or "See Also"

### **Code Blocks:**
- Always specify language
- Include comments
- Show both input and output

### **Links:**
- Use relative paths
- Test all links
- Prefer `[text](./file.md)` over full URLs

---

## 🚫 Anti-Patterns to Avoid

1. **Multiple "Final" Documents**
   - ❌ FINAL_SUMMARY.md, PROJECT_SUMMARY.md, CURRENT_STATUS.md
   - ✅ One README.md + IMPLEMENTATION_LOG.md

2. **Progress Files Without Dates**
   - ❌ IMPLEMENTATION_PROGRESS.md
   - ✅ IMPLEMENTATION_LOG.md with timestamped entries

3. **Redundant Guides**
   - ❌ USAGE_GUIDE.md + DASHBOARD_GUIDE.md + NAVIGATION_GUIDE.md
   - ✅ One USER_GUIDE.md with sections

4. **Scattered "What's New"**
   - ❌ WHATS_NEW.md, TODAYS_PROGRESS.md, SESSION_SUMMARY.md
   - ✅ One CHANGELOG.md with date entries

---

## 📝 Template: IMPLEMENTATION_LOG.md

```markdown
# Implementation Log

Track all implementation work chronologically.

---

## [Feature Name] - YYYY-MM-DD
**Status:** ✅ Complete / 🚧 In Progress / 📋 Planned

### Overview
Brief description.

### What Was Built
- Component 1
- Component 2

### Files Created
- `src/path/file.py`

### Files Modified
- `src/path/existing.py`

### API Endpoints
- `GET /api/endpoint` - Description

### Testing
- ✅ Unit tests pass
- ✅ Integration tests pass
- ✅ UI verified

### Documentation Updated
- [x] API_REFERENCE.md
- [x] USER_GUIDE.md
- [x] CHANGELOG.md

---

## [Next Feature] - YYYY-MM-DD
...
```

---

## 🎯 Goal

**Maintain a clean, organized documentation structure that:**
- Is easy to navigate
- Avoids duplication
- Scales with the project
- Helps both users and developers
- Reduces maintenance burden

---

**Remember:** Documentation is code. Keep it DRY (Don't Repeat Yourself)!
