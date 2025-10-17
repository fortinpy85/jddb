# Phase 4: Quick Start Guide

**For:** Development Team
**Status:** Integration Sprint Complete ✅
**Date:** October 4, 2025

---

## 🚀 What to Do Next

### This Week (Week 1)

```bash
# 1. Internal User Testing
- Recruit 5-10 users
- Provide test job descriptions
- Monitor RLHF events in console
- Gather feedback

# 2. Monitor Pipeline
- Check: SELECT COUNT(*) FROM rlhf_feedback;
- Watch browser console for sync logs
- Review acceptance statistics

# 3. Quick Fixes
- Fix any bugs found
- Improve UX based on feedback
```

---

## 📋 Immediate Checklist

### Day 1-2: User Testing
- [ ] Email invitation to 10 potential testers
- [ ] Create test dataset (5 job descriptions)
- [ ] Set up monitoring dashboard
- [ ] Document test protocol

### Day 3-4: Monitor & Fix
- [ ] Review collected RLHF data
- [ ] Check acceptance rates
- [ ] Fix critical bugs
- [ ] Improve error messages

### Day 5: Planning
- [ ] Analyze test results
- [ ] Prioritize production deployment tasks
- [ ] Plan analytics dashboard
- [ ] Schedule next sprint

---

## 🎯 Key Metrics to Track

**Daily:**
- RLHF events captured: `localStorage.getItem('rlhf_live_events')`
- Sync success rate: Check console logs
- User engagement: Time spent in Live AI tab

**Weekly:**
- Acceptance rate: `GET /api/rlhf/statistics/acceptance-rate`
- Suggestions by type: `GET /api/rlhf/statistics/by-type`
- Database growth: `SELECT COUNT(*) FROM rlhf_feedback`

---

## 💻 Commands & Queries

### Check RLHF Data

**Browser Console:**
```javascript
// Get pending events
import { getPendingRLHFCount } from '@/hooks/useLiveImprovement';
console.log('Pending events:', getPendingRLHFCount());

// Export all events
import { exportAllRLHFData } from '@/hooks/useLiveImprovement';
console.table(exportAllRLHFData());

// Manual sync
import { syncRLHFData } from '@/hooks/useLiveImprovement';
syncRLHFData().then(result => console.log(result));
```

**Database:**
```sql
-- Total RLHF records
SELECT COUNT(*) FROM rlhf_feedback;

-- Acceptance rate
SELECT
  user_action,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM rlhf_feedback
GROUP BY user_action;

-- By suggestion type
SELECT
  suggestion_type,
  user_action,
  COUNT(*) as count
FROM rlhf_feedback
GROUP BY suggestion_type, user_action
ORDER BY suggestion_type, count DESC;
```

**API:**
```bash
# Acceptance rate
curl http://localhost:8000/api/rlhf/statistics/acceptance-rate

# By type
curl http://localhost:8000/api/rlhf/statistics/by-type

# Export training data
curl http://localhost:8000/api/rlhf/export/training-data?min_confidence=0.7
```

---

## 📊 Expected Outcomes

### Week 1 Success
- ✅ 50+ RLHF events captured
- ✅ Zero sync failures
- ✅ Acceptance rate > 30%
- ✅ Positive user feedback

### Week 4 Success
- ✅ Production deployed
- ✅ Analytics dashboard live
- ✅ 500+ RLHF events
- ✅ Model fine-tuning planned

---

## 🐛 Troubleshooting

### RLHF Events Not Syncing

**Check:**
1. localStorage has events: `localStorage.getItem('rlhf_live_events')`
2. Count >= 10 (threshold)
3. Backend running: http://localhost:8000/health
4. Console for errors

**Fix:**
```javascript
// Manual sync
import { syncRLHFData } from '@/hooks/useLiveImprovement';
await syncRLHFData();
```

### Statistics Not Updating

**Check:**
1. Database has records: `SELECT COUNT(*) FROM rlhf_feedback;`
2. Backend server running
3. Migration applied: `poetry run alembic current`

**Fix:**
```bash
# Restart backend
cd backend && make server

# Check migration
poetry run alembic current
# Should show: add_rlhf_feedback (head)
```

### Frontend Not Loading

**Check:**
1. Frontend server: http://localhost:3000/
2. Backend API: http://localhost:8000/api/docs
3. Console for errors

**Fix:**
```bash
# Restart frontend
bun dev

# Clear cache
rm -rf .next node_modules/.cache
bun install
```

---

## 📁 Key Files Reference

**Frontend:**
- `src/components/improvement/ImprovementView.tsx` - Live AI integration
- `src/hooks/useLiveImprovement.ts` - RLHF capture logic
- `src/lib/api.ts` - Sync method

**Backend:**
- `backend/src/jd_ingestion/database/models.py` - RLHFFeedback model
- `backend/src/jd_ingestion/api/endpoints/rlhf.py` - API endpoints
- `backend/src/jd_ingestion/services/rlhf_service.py` - Business logic

**Documentation:**
- `archive/INTEGRATION_SPRINT_COMPLETE.md` - Full implementation details
- `archive/INTEGRATION_SPRINT_SUMMARY.md` - Executive summary
- `NEXT_STEPS.md` - Roadmap for remaining work

---

## 🔗 Quick Links

**Servers:**
- Frontend: http://localhost:3000/
- Backend: http://localhost:8000/
- API Docs: http://localhost:8000/api/docs

**Dashboards:**
- Acceptance Rate: `GET /api/rlhf/statistics/acceptance-rate`
- By Type: `GET /api/rlhf/statistics/by-type`

**Export:**
- Training Data: `GET /api/rlhf/export/training-data?min_confidence=0.7&limit=1000`

---

## 🎯 Next Session

**When continuing, start with:**

1. Review test results from internal users
2. Analyze RLHF data patterns
3. Plan production deployment
4. Design analytics dashboard

**Command:** `Check RLHF statistics and review user feedback`

---

*Quick Start Guide - Phase 4*
*Last Updated: October 4, 2025*
