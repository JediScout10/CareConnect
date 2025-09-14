// meditation\static\meditation\js\script.js
document.addEventListener("DOMContentLoaded", function () {
    let timer;
    let seconds = 0;
    
    function startMeditation() {
        document.getElementById("status").innerText = "Meditation session started!";
        seconds = 0; 
        clearInterval(timer); 
        timer = setInterval(updateTimer, 1000);
    }

    function updateTimer() {
        seconds++;
        document.getElementById("timer").innerText = `Time: ${seconds} sec`;
    }

    function stopMeditation() {
        clearInterval(timer);
        document.getElementById("status").innerText = "Meditation session stopped!";
    }

    // Attach event listeners to buttons
    document.getElementById("startButton").addEventListener("click", startMeditation);
    document.getElementById("stopButton").addEventListener("click", stopMeditation);
});

