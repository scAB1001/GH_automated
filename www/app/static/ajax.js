document.addEventListener('DOMContentLoaded', function () {
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const carId = this.getAttribute('data-car-id');
            let liked = this.getAttribute('data-liked') === 'true';
            const likeCountDisplay = document.querySelector('.like-count[data-car-id="' + carId + '"]');

            fetch('/toggle_count/' + carId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ liked: !liked })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                } else {
                    likeCountDisplay.textContent = data.like_count;
                    this.setAttribute('data-liked', (!liked).toString());
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        });
    });
});
