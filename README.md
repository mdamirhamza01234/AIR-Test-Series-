# VP AIR Test Series - Offline Android App

Is repo ko GitHub par push karte hi APK khud ban jata hai. Aapki PDF aur HTML files APK ke andar
bundle ho jati hain, isliye app mein internet ki zaroorat nahi padti.

## Steps

1. Apni 30 files (papers, keys, mock tests) `files/` folder mein daalo. Naam ke rules `files/README.txt` mein hain.
2. Poora folder GitHub repo mein upload karo (`.github` folder bhi, usi mein build workflow hai).
3. GitHub par **Actions** tab kholo, **Build APK** run hone do (kuch minute lagte hain).
4. Run khatam hone par neeche **Artifacts** mein `VP-AIR-app` download karo, usme `app-debug.apk` hai.
5. APK phone mein install karo (Unknown sources allow karna padega).

## Menu aur Test Records

- Upar left ke hamburger menu (3 lines) se **Home** aur **Test Records** khulte hain.
- Mock test mein **Submit Test** dabate hi result apne aap save ho jata hai (score, subject-wise marks, har question ka jawab, time taken).
- Record par tap karo to poora breakdown dikhta hai: question map, sahi/galat/skip wale questions ki list.
- Home par har set ke card mein aapka best score aur attempts bhi dikhte hain.
- Records phone ke andar save hote hain. App uninstall karne ya app ka data clear karne par ud jayenge.
- Test chalte waqt back button dabane par app puchta hai ki test chhodna hai ya nahi.

## Notes

- Build log mein dikhta hai ki har file kis set aur kis type (paper/key/mock) mein gayi, galat lage to file ka naam badal ke dobara push karo.
- Browser se upload karte waqt GitHub har file par 25 MB ki limit lagata hai. Badi file ho to git ya GitHub Desktop se push karo (limit 100 MB).
- PDF app ke andar khulte hain (pinch-zoom chalta hai), mock test HTML bhi app ke andar chalte hain.
- Phone ka back button se peeche aa sakte ho.
- Ye debug APK hai, personal use ke liye theek hai. Play Store ke liye alag signed build chahiye hoga.
