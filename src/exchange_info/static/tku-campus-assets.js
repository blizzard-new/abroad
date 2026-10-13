// TKU's reviewed, licensed campus photos take precedence within its catalogue.
// The shared map, image manifest, and other university lookups stay reusable.
(() => {
  const sharedImageLookup = window.schoolImageFor;
  window.schoolImageFor = function tkuCampusImage(schoolName, country = null) {
    if (typeof document !== "undefined") document.body.toggleAttribute("data-tku-campus-assets", state.dashboard?.school_name === "淡江大學");
    if (state.dashboard?.school_name !== "淡江大學") {
      return sharedImageLookup(schoolName, country);
    }
    const partner = state.dashboard.partner_universities.find((row) =>
      normalize(row.school_name) === normalize(schoolName) && (!country || row.country === country));
    const evidence = partner?.reference_data;
    if (partner?.image_status !== "verified" || !partner.image_url || !evidence?.campus_photo_author) return undefined;
    return {
      school_name: partner.school_name, country: partner.country, status: "verified",
      local_path: partner.image_url, official_page_url: partner.image_page_url,
      image_source_url: partner.image_source_url, license_name: evidence.campus_photo_license,
      license_url: evidence.campus_photo_license_url,
      note: `攝影：${evidence.campus_photo_author} · ${evidence.campus_photo_license} · ${evidence.campus_photo_modification_note || "本次未另行修改照片"}；${evidence.campus_photo_date ? `拍攝期${evidence.campus_photo_date}；` : ""}${evidence.campus_photo_campus_pair_mismatch === "different_campuses" ? "校景與地圖為不同校區；" : ""}校區與拍攝期見圖片來源。`,
    };
  };
})();
