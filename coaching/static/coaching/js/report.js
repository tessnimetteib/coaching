// coaching/static/coaching/js/report.js
// Expects a script tag with id="assessment-data" containing the JSON object

(function(){
  const dataEl = document.getElementById("assessment-data");
  if (!dataEl) return;
  const data = JSON.parse(dataEl.textContent || "{}");

  // Big Five radar
  const bf = data.big_five || {
    openness: 16, conscientiousness: 14, extraversion: 10, agreeableness: 18, stability: 13
  };
  const labels = ["Ouverture", "Conscienciosité", "Extraversion", "Agréabilité", "Stabilité"];
  const values = [
    bf.openness || bf["openness"] || 0,
    bf.conscientiousness || bf["conscientiousness"] || 0,
    bf.extraversion || bf["extraversion"] || 0,
    bf.agreeableness || bf["agreeableness"] || 0,
    bf.stability || bf["stability"] || bf["emotional_stability"] || 0
  ];

  const radarEl = document.getElementById("bigFiveRadar");
  if (radarEl) {
    const ctx = radarEl.getContext("2d");
    new Chart(ctx, {
      type: "radar",
      data: {
        labels: labels,
        datasets: [{
          label: "Big Five (score)",
          data: values,
          backgroundColor: "rgba(99,102,241,0.15)",
          borderColor: "rgba(99,102,241,0.9)",
          pointBackgroundColor: "rgba(139,92,246,0.9)",
        }]
      },
      options: {
        scales: {
          r: {
            min: 0,
            max: 25,
            ticks: { stepSize: 5 }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // DISC bar
  const disc = data.disc || {D:6,I:9,S:8,C:7};
  const discEl = document.getElementById("discChart");
  if (discEl) {
    const discCtx = discEl.getContext("2d");
    new Chart(discCtx, {
      type: "bar",
      data: {
        labels: ["D","I","S","C"],
        datasets: [{
          label: "DISC",
          data: [disc.D||0, disc.I||0, disc.S||0, disc.C||0],
          backgroundColor: ["#ef4444","#f59e0b","#10b981","#3b82f6"]
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  // Recommendations populate
  const recList = document.getElementById("recommendations");
  if (recList && Array.isArray(data.recommendations)) {
    data.recommendations.forEach((r) => {
      const li = document.createElement("li");
      li.className = "list-group-item";
      li.textContent = typeof r === "string" ? r : (r.text || JSON.stringify(r));
      recList.appendChild(li);
    });
  }
})();