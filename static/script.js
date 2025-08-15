document.addEventListener("DOMContentLoaded", function() {
    const circles = document.querySelectorAll('.progress-circle');
    circles.forEach(function(circle){
        const percent = circle.getAttribute('data-percent');
        const angle = percent * 3.6;
        circle.style.background = `conic-gradient(#2ecc71 ${angle}deg, #eef7f0 0deg)`;
    });
    console.log("Resume Analyzer JS Loaded!");
});
