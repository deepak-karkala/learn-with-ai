# 📋 Staging Setup Checklist

## 🔍 Verification Steps for Vercel Preview Deployment

### **1. GitHub Secrets Verification**

**Check Repository Settings → Secrets and variables → Actions:**

- [ ] `VERCEL_TOKEN` ✅ (should already exist)
- [ ] `ORG_ID` ✅ (should already exist)  
- [ ] `PROJECT_ID` ✅ (should already exist)
- [ ] `GITHUB_TOKEN` ✅ (auto-provided by GitHub)

**If any are missing, get them via:**
```bash
# Get Vercel Token
npm i -g vercel
vercel login
vercel tokens create "GitHub Actions"

# Get ORG_ID and PROJECT_ID
cd your-project
vercel link
cat .vercel/project.json  # Contains orgId and projectId
```

### **2. Vercel Project Configuration**

**Go to Vercel Dashboard → Your Project:**

#### **Environment Variables Setup:**
- [ ] **Production Environment** (for main branch):
  ```
  GOOGLE_API_KEY=your_production_key
  DEBUG=false
  NODE_ENV=production
  ```

- [ ] **Preview Environment** (for develop branch):
  ```
  GOOGLE_API_KEY=your_staging_key  
  DEBUG=true
  NODE_ENV=preview
  ```

#### **Git Integration Settings:**
- [ ] **Production Branch:** `main`
- [ ] **Preview Deployments:** ✅ Enabled
- [ ] **Deploy all branches:** ✅ Enabled

### **3. Test the Staging Deployment**

#### **Create Test Deploy:**
```bash
# 1. Create test branch
git checkout develop
git checkout -b test-staging-setup
echo "Testing staging setup" > STAGING_TEST.md
git add . && git commit -m "test: staging deployment setup"
git push origin test-staging-setup

# 2. Merge to develop to trigger staging
git checkout develop  
git merge test-staging-setup
git push origin develop
```

#### **Verify Results:**
- [ ] GitHub Actions "Staging Deployment" workflow runs successfully
- [ ] Check **Actions** tab for workflow logs
- [ ] Look for preview URL in workflow output
- [ ] Verify deployment appears in Vercel dashboard
- [ ] Test the preview URL works

### **4. Expected Workflow Output**

**In GitHub Actions logs, you should see:**
```
🚀 Preview Deployment Successful!
🔗 Preview URL: https://your-project-git-develop-yourname.vercel.app
📋 Staging Environment Ready for Testing
🎯 Environment: develop branch → preview deployment
```

### **5. Vercel Dashboard Verification**

**In Vercel Dashboard → Deployments:**
- [ ] New deployment appears with "Preview" label
- [ ] Deployment source shows `develop` branch
- [ ] Preview URL is accessible and loads correctly
- [ ] Backend API endpoints work (check `/api/health`)

### **6. Environment-Specific Testing**

**Test that staging environment works correctly:**
- [ ] Frontend loads without errors
- [ ] API endpoints respond (test `/api/health`)
- [ ] Environment variables are correct (staging values, not production)
- [ ] Debug mode is enabled (if applicable)
- [ ] No production data is accessible

## 🚨 **Troubleshooting Guide**

### **Issue: Deployment Fails**
```bash
# Check these:
1. Verify all GitHub secrets are set correctly
2. Check Vercel project is linked to correct repository
3. Ensure vercel.json configuration is valid
4. Review GitHub Actions error logs
```

### **Issue: No Preview URL in Output**
```bash
# Add debug step to workflow:
- name: Debug Vercel Outputs
  run: |
    echo "All outputs: ${{ toJson(steps.vercel-deploy.outputs) }}"
```

### **Issue: Environment Variables Not Working**
```bash
# In Vercel Dashboard:
1. Go to Project → Settings → Environment Variables
2. Ensure "Preview" environment is configured
3. Check that variable names match exactly
4. Redeploy if variables were added after deployment
```

### **Issue: Build Failures**
```bash
# Common fixes:
1. Verify Node.js version compatibility
2. Check that build commands work locally
3. Ensure all dependencies are in package.json
4. Review vercel.json build configuration
```

## ✅ **Success Criteria**

**Your staging setup is complete when:**

1. **Automated Deployment:** Push to `develop` automatically creates preview
2. **Preview URL:** You get a working preview URL for testing
3. **Environment Isolation:** Staging uses separate environment variables
4. **Fast Deployment:** No redundant CI tests, just direct deployment
5. **Integration Testing:** Full-stack preview with frontend + backend

## 🎯 **Next Steps After Setup**

1. **Document the staging URL pattern** for your team
2. **Add staging environment testing** to your workflow documentation  
3. **Set up monitoring** for staging deployments (optional)
4. **Configure custom domain** for staging if desired (optional)

## 📞 **Need Help?**

If you encounter issues:
1. Check the detailed setup guide: [vercel-preview-setup.md](./vercel-preview-setup.md)
2. Review Vercel documentation: https://vercel.com/docs/deployments/preview-deployments
3. Check GitHub Actions documentation for the Vercel action

---

**Once this checklist is complete, your `develop` branch will automatically deploy to a preview environment for seamless staging testing! 🚀**