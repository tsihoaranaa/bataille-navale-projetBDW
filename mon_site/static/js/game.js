document.addEventListener("DOMContentLoaded", () => {
    const startButton = document.getElementById("start-game");
    const fireButton = document.getElementById("fire");
    const nextTurnButton = document.getElementById("next-turn");
    const pauseButton = document.getElementById("pause-game");
    const notification = document.getElementById("notification");

    startButton.addEventListener("click", () => {
        notification.textContent = "La partie commence !";
        startButton.disabled = true;
        fireButton.disabled = false;
    });

    fireButton.addEventListener("click", () => {
        notification.textContent = "Tir effectué !";
        fireButton.disabled = true;
        nextTurnButton.disabled = false;
    });

    nextTurnButton.addEventListener("click", () => {
        notification.textContent = "Tour suivant...";
        nextTurnButton.disabled = true;
        fireButton.disabled = false;
    });

    pauseButton.addEventListener("click", () => {
        notification.textContent = "Partie suspendue.";
    });
});