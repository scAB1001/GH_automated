// Source: https://github.com/CodeSteppe/card-swiper

// DOM
const swiper = document.querySelector('#swiper');
const like = document.querySelector('#like');
const dislike = document.querySelector('#dislike');

// Variables
let cardCount = 0;

// Functions
function appendNewCard(carData) {
  const card = new Card({
    carID: carData.carID,
    imageUrl: carData.imageUrl,
    carName: carData.carName,
    details: carData.details,
    
    onDismiss: () => {
      cardCount--;  // Find empty card
      console.log(`cardCount: ${cardCount}`);
      if (cardCount <= 0) {
        cardsEmpty();
      }
      appendNewCard;
    },
    onLike: () => {
      console.log(`${carData.carName} liked`); // CONFIRMATION
      like.style.animationPlayState = 'running';
      like.classList.toggle('trigger');
    },
    onDislike: () => {
      console.log(`${carData.carName} disliked`); // CONFIRMATION
      dislike.style.animationPlayState = 'running';
      dislike.classList.toggle('trigger');
    }

  });
  
  cardCount++;  // For the number of cards
  console.log(`card${cardCount} added`);  
  swiper.append(card.element);

  const cards = swiper.querySelectorAll('.card:not(.dismissing)');
  cards.forEach((card, index) => {
    card.style.setProperty('--i', index);
  });
}

// Load the initial cards
cars.forEach((carData) => {
  appendNewCard(carData);
});

function cardsEmpty() {
  console.log("All cards have been swiped!");
  fetch('/cards-depleted', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ isEmpty: true })
    })
    .then(response => response.json())
    .then(data =>{
      console.log(data);
      document.getElementById('no-more-cards-message').style.display = 'block';
    })
    .catch(error => console.error('Error:', error));

}