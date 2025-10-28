# Permanent Alembic Setup - Complete Configuration

## ✅ What Was Fixed

The Alembic setup has been completely overhauled to provide a **permanent, production-ready solution**. All configuration issues have been resolved.

---

## 📁 Files Modified

### 1. `alembic.ini`
**Changes:**
- Removed invalid `sqlalchemy.url = %(DB_URL)s`
- Added `prepend_sys_path = .`
- Database URL now set dynamically in `env.py`

### 2. `alembic/env.py`
**Major improvements:**
- ✅ Proper DATABASE_URL handling from environment or config
- ✅ Explicit imports of all models for better autogenerate
- ✅ Added `compare_type=True` and `compare_server_default=True`
- ✅ Added `render_as_batch=True` for SQLite compatibility
- ✅ Better error messages and validation
- ✅ Safe database URL masking in output

### 3. `alembic/versions/5bc86fd614bc_test.py`
**Fixes:**
- Changed `branch_labels = 'None'` → `branch_labels = None`
- Changed `depends_on = 'None'` → `depends_on = None`

### 4. `README.md`
**Added:**
- Database migrations section with quick start
- Helper script examples
- Links to documentation

---

## 📄 New Files Created

1. **ALEMBIC_GUIDE.md** - Comprehensive migration guide
2. **ALEMBIC_QUICK_REF.md** - Quick reference card
3. **ALEMBIC_FIXES_SUMMARY.md** - Detailed changelog
4. **alembic_helpers.py** - Convenience wrapper script
5. **ALEMBIC_SETUP.md** - This file

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Set your database URL
export DATABASE_URL="postgresql://user:password@localhost/dbname"
```

### 2. Check Status
```bash
alembic current
# or use helper
python alembic_helpers.py status
```

### 3. Create Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add new feature"
# or
python alembic_helpers.py autogenerate "add new feature"
```

### 4. Apply Migration
```bash
alembic upgrade head
# or
python alembic_helpers.py upgrade
```

---

## 🎯 Usage Examples

### Adding a New Column
```python
# 1. Edit app/models.py
class User(Base):
    # ... existing fields
    new_field = Column(String, nullable=True)  # Add this
```

```bash
# 2. Generate migration
alembic revision --autogenerate -m "add new_field to users"

# 3. Review generated file in alembic/versions/

# 4. Apply it
alembic upgrade head
```

### Adding a New Model
```python
# 1. Add to app/models.py
class NewModel(Base):
    __tablename__ = "new_models"
    id = Column(String, primary_key=True)
    name = Column(String)
```

```bash
# 2. Generate and apply
alembic revision --autogenerate -m "add NewModel"
alembic upgrade head
```

### Modifying Existing Field
```python
# 1. Edit in app/models.py
class User(Base):
    email = Column(String, unique=True, index=True, nullable=False)  # Add nullable=False
```

```bash
# 2. Generate and apply
alembic revision --autogenerate -m "make email not null"
alembic upgrade head
```

---

## 🛠️ Helper Script Usage

```bash
# Check status
python alembic_helpers.py status

# Create migration
python alembic_helpers.py autogenerate "description"

# Apply all
python alembic_helpers.py upgrade

# Apply next only
python alembic_helpers.py upgrade +1

# Rollback last
python alembic_helpers.py downgrade -1

# Rollback all
python alembic_helpers.py downgrade base

# Show history
python alembic_helpers.py history
```

---

## 📋 Command Reference

### Status & History
```bash
alembic current         # Show current revision
alembic heads          # Show all head revisions
alembic history        # Show full history
alembic history -v     # Verbose history
```

### Create Migrations
```bash
# Auto-generate (RECOMMENDED)
alembic revision --autogenerate -m "description"

# Manual migration
alembic revision -m "description"

# Empty migration for custom SQL
alembic revision -m "custom changes"
```

### Apply Migrations
```bash
alembic upgrade head     # Apply all pending
alembic upgrade +1       # Apply next only
alembic upgrade <rev>     # Upgrade to revision
```

### Rollback Migrations
```bash
alembic downgrade -1      # Rollback one
alembic downgrade <rev>   # Rollback to revision
alembic downgrade base    # Rollback all
```

### View SQL
```bash
alembic upgrade head --sql    # Show SQL without executing
alembic upgrade head --sql > migration.sql  # Save to file
```

---

## 🔧 Configuration Details

### Database URL Detection Order
1. Environment variable `DATABASE_URL`
2. Import from `app.config.DATABASE_URL`
3. Raise error if neither found

### Model Import Strategy
All models are explicitly imported in `alembic/env.py`:
- User
- OutstandingToken
- BlacklistToken
- Document
- ChatHistory
- Hr_Document
- SubscriptionPlan
- UserSubscription
- UsageTracking
- DynamicPrompt
- ProcessedDocument
- Resume
- JobRequirement
- ResumeMatch
- ChatDocument

### Autogenerate Settings
```python
compare_type=True              # Detect type changes
compare_server_default=True    # Detect default changes
render_as_batch=True          # SQLite batch mode
```

---

## ⚠️ Important Notes

### Do's ✅
- Always review autogenerated migrations
- Test on development database first
- Use descriptive migration messages
- Keep migrations in version control
- Backup production database before migrations

### Don'ts ❌
- Don't edit existing migration files
- Don't skip reviewing autogenerated migrations
- Don't run migrations in production without backup
- Don't manually edit alembic_version table

---

## 🐛 Troubleshooting

### "DATABASE_URL not set"
```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

### "Can't locate revision"
```bash
# Check revision chain
alembic history
alembic current

# If stuck, stamp current state
alembic stamp head
```

### "Target database is not up to date"
```bash
# Apply pending migrations
alembic upgrade head
```

### "Import error: No module named 'app'"
```bash
# Run from project root
cd /path/to/Multi_tool_chatbot
alembic upgrade head
```

### "Multiple heads detected"
```bash
# Merge heads
alembic merge -m "merge heads" heads
```

---

## 📊 Migration Workflow

```
1. Edit Models
   ↓
2. Generate Migration
   ↓
3. Review Migration File
   ↓
4. Test on Dev Database
   ↓
5. Commit to Git
   ↓
6. Apply to Production
```

---

## 📚 Documentation Files

| File | Description |
|------|-------------|
| `ALEMBIC_GUIDE.md` | Complete guide with workflows |
| `ALEMBIC_QUICK_REF.md` | Quick command reference |
| `ALEMBIC_FIXES_SUMMARY.md` | Detailed changelog |
| `ALEMBIC_SETUP.md` | This setup documentation |
| `README.md` | Main project readme (updated) |

---

## 🎓 Learning Resources

1. **Alembic Official Docs:** https://alembic.sqlalchemy.org/
2. **SQLAlchemy Migrations:** https://docs.sqlalchemy.org/en/14/core/metadata.html
3. **Project Guides:** See `ALEMBIC_GUIDE.md`

---

## 🏁 Summary

The Alembic setup is now:
- ✅ Properly configured for PostgreSQL
- ✅ Supports SQLite (batch mode)
- ✅ Automatic model detection
- ✅ Environment-aware (reads DATABASE_URL)
- ✅ Production-ready
- ✅ Well-documented
- ✅ Easy to use with helper scripts

You can now confidently manage database schema changes!

