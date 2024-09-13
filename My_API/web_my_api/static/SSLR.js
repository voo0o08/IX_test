let rain_speed = 1000 // 몇초마다 단어들이 아래로 떨어지는지
let new_sec = 5000 // 몇초마다 단어들이 생성되는지

alert('게임을 시작합니다!👏🏻')
const words = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
const container = document.querySelector('#container');

function getRandomInt(minimum, maximum) {
  const min = Math.ceil(minimum);
  const max = Math.floor(maximum);
  return Math.floor(Math.random() * (max - min)) + min; 
}

// 단어 초기화 
function init() {
  const maxPositionX = container.offsetWidth - 90;
  // for (let word of words) {
  //   createWord(word, getRandomInt(20, maxPositionX));
  // }
}

function createWord(text, leftPosition) {
  const span = document.createElement('span');
  span.classList.add('word');
  span.style.top = `20px`;
  span.style.left = `${leftPosition}px`;
  span.dataset.word = text;
  span.textContent = text;
  container.append(span);
}

init();
// initializer 끝 

const input = document.querySelector('#input');

function checker() {
  const words = document.querySelectorAll('.word');
  if (words.length === 0) {
    alert('Success!👏🏻');
    if(confirm('retry?')) {
      window.location.reload();
    }
  }
}

function removeWord() {
  const word = document.querySelector(`[data-word="${input.value}"]`);
  if (word) {
    word.remove();
    checker();
  }
  input.value = '';
}

input.addEventListener('change', removeWord);

// 단어들이 아래로 떨어지게 하는 함수
function moveWordsDown() {
  const words = document.querySelectorAll('.word');
  const maxPositionY = container.offsetHeight - 40;
  words.forEach(word => {
    let currentTop = parseInt(word.style.top);
    word.style.top = `${currentTop + 20}px`;
    if (currentTop + 20 >= maxPositionY) {
      word.remove();
      checker();
    }
  });
}

// 1초마다 단어들이 아래로 떨어지게 설정
setInterval(moveWordsDown, rain_speed);

// 새로운 단어를 생성하는 함수
function addNewWord() {
  const maxPositionX = container.offsetWidth - 90;
  const newWord = words[getRandomInt(0, words.length)];
  createWord(newWord, getRandomInt(20, maxPositionX));
}

// 바로 첫 단어 생성
addNewWord();

// 5초마다 새로운 단어 생성
setInterval(addNewWord, new_sec);

// 카메라 
const userFaceElement = document.getElementById('video');

navigator.mediaDevices.getUserMedia({ video: true })
  .then(function(stream) {
    userFaceElement.srcObject = stream;
    userFaceElement.play();
  })
  .catch(function(err) {
    console.error('웹캠에 접근할 수 없습니다.', err); 
  });

document.getElementById("captureButton").addEventListener("click", function() {
  fetch("/capture")
    .then(response => response.json())
    .then(data => {
      const prediction = data.prediction;
      const word = document.querySelector(`[data-word="${prediction}"]`);
      if (word) {
        word.remove();
        checker();
      }
    })
    .catch(error => console.error(error));
});
