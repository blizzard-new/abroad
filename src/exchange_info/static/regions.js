/* Which part of the world each country is in, so a student can look for "東歐" or "Europe" and not only for one country.
   DOM-free: the school list uses it for the region filter, the grouped country list and the search words. */
(function (root) {
  "use strict";

  // [Chinese name, English name, ...other words a student might type]
  const COUNTRIES = {
    "east-asia": [
      ["大陸地區", "China", "中國", "中國大陸", "中華人民共和國", "mainland"], ["中國", "China"], ["中國大陸", "China", "mainland"],
      ["香港", "Hong Kong"], ["澳門", "Macau"], ["臺灣", "Taiwan", "台灣"], ["日本", "Japan"], ["韓國", "South Korea", "Korea", "南韓"], ["南韓", "South Korea", "Korea", "韓國"], ["蒙古", "Mongolia"],
    ],
    "southeast-asia": [
      ["越南", "Vietnam"], ["泰國", "Thailand"], ["印尼", "Indonesia"], ["菲律賓", "Philippines"], ["馬來西亞", "Malaysia"],
      ["新加坡", "Singapore"], ["柬埔寨", "Cambodia"], ["緬甸", "Myanmar"], ["寮國", "Laos"], ["汶萊", "Brunei"],
    ],
    "south-asia": [["印度", "India"], ["孟加拉", "Bangladesh"], ["斯里蘭卡", "Sri Lanka"], ["尼泊爾", "Nepal"], ["巴基斯坦", "Pakistan"]],
    "west-asia": [
      ["哈薩克", "Kazakhstan", "中亞"], ["烏茲別克", "Uzbekistan", "中亞"], ["吉爾吉斯", "Kyrgyzstan", "中亞"],
      ["土耳其", "Turkey", "Türkiye", "Turkiye", "歐亞"], ["以色列", "Israel"], ["約旦", "Jordan"], ["阿聯", "UAE", "United Arab Emirates", "阿拉伯聯合大公國"],
      ["沙烏地阿拉伯", "Saudi Arabia", "沙烏地"], ["卡達", "Qatar"], ["伊朗", "Iran"], ["喬治亞", "Georgia"], ["亞美尼亞", "Armenia"],
    ],
    "eastern-europe": [
      ["波蘭", "Poland"], ["捷克", "Czech Republic", "Czechia"], ["斯洛伐克", "Slovakia"], ["匈牙利", "Hungary"], ["羅馬尼亞", "Romania"],
      ["保加利亞", "Bulgaria"], ["立陶宛", "Lithuania", "波羅的海"], ["拉脫維亞", "Latvia", "波羅的海"], ["愛沙尼亞", "Estonia", "波羅的海"],
      ["俄羅斯", "Russia"], ["烏克蘭", "Ukraine"], ["白俄羅斯", "Belarus"], ["阿爾巴尼亞", "Albania", "巴爾幹"], ["塞爾維亞", "Serbia", "巴爾幹"],
      ["克羅埃西亞", "Croatia", "巴爾幹"], ["斯洛維尼亞", "Slovenia", "巴爾幹"], ["波士尼亞", "Bosnia", "巴爾幹"], ["北馬其頓", "North Macedonia", "巴爾幹"],
      ["蒙特內哥羅", "Montenegro", "巴爾幹"], ["摩爾多瓦", "Moldova"], ["科索沃", "Kosovo", "巴爾幹"],
    ],
    "western-europe": [
      ["法國", "France"], ["德國", "Germany", "中歐"], ["荷蘭", "Netherlands", "Holland"], ["比利時", "Belgium"], ["盧森堡", "Luxembourg"],
      ["奧地利", "Austria", "中歐"], ["瑞士", "Switzerland", "中歐"], ["英國", "United Kingdom", "UK", "England", "Britain"], ["愛爾蘭", "Ireland"],
    ],
    "northern-europe": [["瑞典", "Sweden", "Scandinavia"], ["挪威", "Norway", "Scandinavia"], ["丹麥", "Denmark", "Scandinavia"], ["芬蘭", "Finland"], ["冰島", "Iceland"]],
    "southern-europe": [["西班牙", "Spain"], ["義大利", "Italy"], ["葡萄牙", "Portugal"], ["希臘", "Greece"], ["馬爾他", "Malta"], ["賽普勒斯", "Cyprus"]],
    "north-america": [["美國", "United States", "USA", "America"], ["加拿大", "Canada"], ["墨西哥", "Mexico"]],
    "latin-america": [
      ["巴西", "Brazil"], ["阿根廷", "Argentina"], ["智利", "Chile"], ["哥倫比亞", "Colombia"], ["秘魯", "Peru"], ["烏拉圭", "Uruguay"],
      ["厄瓜多", "Ecuador"], ["古巴", "Cuba"], ["巴拿馬", "Panama"], ["哥斯大黎加", "Costa Rica"], ["瓜地馬拉", "Guatemala"],
    ],
    "oceania": [["澳洲", "Australia", "澳大利亞"], ["澳大利亞", "Australia", "澳洲"], ["紐西蘭", "New Zealand"], ["斐濟", "Fiji"]],
    "africa": [
      ["摩洛哥", "Morocco"], ["南非", "South Africa"], ["埃及", "Egypt"], ["肯亞", "Kenya"], ["迦納", "Ghana"], ["突尼西亞", "Tunisia"],
      ["奈及利亞", "Nigeria"], ["衣索比亞", "Ethiopia"], ["坦尚尼亞", "Tanzania"], ["塞內加爾", "Senegal"],
    ],
  };

  // Display order. A region with `parent` sits under that group in the drop-down; a group (`kids`) selects all of its regions.
  const REGIONS = [
    { id: "europe", label: "歐洲（全部）", kids: ["eastern-europe", "western-europe", "northern-europe", "southern-europe"], words: ["歐洲", "europe", "european"], also: ["土耳其"] },
    { id: "eastern-europe", label: "東歐／中歐", parent: "europe", words: ["東歐", "中歐", "eastern europe", "central europe", "central and eastern europe", "cee"] },
    { id: "western-europe", label: "西歐", parent: "europe", words: ["西歐", "western europe"] },
    { id: "northern-europe", label: "北歐", parent: "europe", words: ["北歐", "northern europe", "nordic"] },
    { id: "southern-europe", label: "南歐", parent: "europe", words: ["南歐", "southern europe"] },
    { id: "asia", label: "亞洲（全部）", kids: ["east-asia", "southeast-asia", "south-asia", "west-asia"], words: ["亞洲", "asia", "asian"] },
    { id: "east-asia", label: "東亞", parent: "asia", words: ["東亞", "east asia"] },
    { id: "southeast-asia", label: "東南亞", parent: "asia", words: ["東南亞", "southeast asia", "south-east asia", "asean"] },
    { id: "south-asia", label: "南亞", parent: "asia", words: ["南亞", "south asia"] },
    { id: "west-asia", label: "中亞／西亞", parent: "asia", words: ["西亞", "中亞", "west asia", "central asia", "middle east", "中東"] },
    { id: "americas", label: "美洲（全部）", kids: ["north-america", "latin-america"], words: ["美洲", "americas"] },
    { id: "north-america", label: "北美", parent: "americas", words: ["北美", "north america"] },
    { id: "latin-america", label: "中南美洲", parent: "americas", words: ["中南美", "南美", "拉丁美洲", "latin america", "south america"] },
    { id: "oceania", label: "大洋洲", words: ["大洋洲", "oceania", "紐澳"] },
    { id: "africa", label: "非洲", words: ["非洲", "africa"] },
  ];
  const OTHER = { id: "other", label: "其他地區", words: [] };

  const byId = new Map([...REGIONS, OTHER].map((region) => [region.id, region]));
  const regionOfCountry = new Map();
  const wordsOfCountry = new Map();
  for (const [regionId, rows] of Object.entries(COUNTRIES)) {
    for (const [name, ...words] of rows) {
      if (!regionOfCountry.has(name)) regionOfCountry.set(name, regionId);
      wordsOfCountry.set(name, [...(wordsOfCountry.get(name) || []), ...words]);
    }
  }
  const alsoIn = new Map();
  for (const region of REGIONS) for (const country of region.also || []) alsoIn.set(country, [...(alsoIn.get(country) || []), region.id]);

  const normalize = (value) => String(value ?? "").toLowerCase().replace(/\s+/g, " ").trim();
  const isRegion = (id) => byId.has(id) && id !== "other";
  const leafOf = (country) => regionOfCountry.get(String(country || "").trim()) || "other";

  /** The ids a country counts under: its own region, that region's group, and any group it is also listed in. */
  function idsOf(country) {
    const leaf = leafOf(country);
    const ids = [leaf];
    const parent = byId.get(leaf)?.parent;
    if (parent) ids.push(parent);
    return [...ids, ...(alsoIn.get(String(country || "").trim()) || [])];
  }

  function inRegion(country, regionId) {
    return !regionId || idsOf(country).includes(regionId);
  }

  /** Region names, their everyday words and the English country name, lower-cased, for the search box to match against. */
  function searchText(country) {
    const name = String(country || "").trim();
    const parts = [];
    for (const id of idsOf(name)) {
      const region = byId.get(id);
      parts.push(region.label, ...region.words);
    }
    parts.push(...(wordsOfCountry.get(name) || []));
    return normalize(parts.join(" "));
  }

  /** The region drop-down: groups of options, only for regions that have at least one of these countries. */
  function regionGroups(countries) {
    const present = new Set();
    for (const country of countries) for (const id of idsOf(country)) present.add(id);
    const groups = [];
    for (const region of REGIONS) {
      if (!present.has(region.id)) continue;
      if (region.kids) groups.push({ id: region.id, label: region.label.replace("（全部）", ""), options: [{ id: region.id, label: region.label }] });
      else if (region.parent) groups.find((group) => group.id === region.parent).options.push({ id: region.id, label: region.label });
      else groups.push({ id: region.id, label: region.label, options: [{ id: region.id, label: region.label }] });
    }
    // A group with a single region in it ("美洲" with only 北美) needs no "all of it" line.
    for (const group of groups) {
      if (group.options.length === 2 && byId.get(group.id)?.kids) group.options.shift();
    }
    return groups;
  }

  /** The country drop-down: the countries split by region, in the order of the region list. */
  function countryGroups(countries) {
    const buckets = new Map();
    for (const country of [...new Set(countries)].sort((a, b) => a.localeCompare(b, "zh-Hant"))) {
      const id = leafOf(country);
      if (!buckets.has(id)) buckets.set(id, []);
      buckets.get(id).push(country);
    }
    const order = [...REGIONS.filter((region) => !region.kids), OTHER];
    return order.filter((region) => buckets.has(region.id)).map((region) => ({ id: region.id, label: region.label, countries: buckets.get(region.id) }));
  }

  const api = { REGIONS, COUNTRIES, isRegion, regionOf: leafOf, inRegion, searchText, regionGroups, countryGroups };
  root.UniWayRegions = api;
  if (typeof module !== "undefined") module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
