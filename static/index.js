function like(postId) {
    const likeButton = document.getElementById(`like-button-${postId}`);
    const likeCount = document.getElementById(`like-count-${postId}`);

    fetch(`/like-post/${postId}`, {method:'POST'}).then((res) => res.json()).then((data) => {
        likeCount.innerHTML = data['likes'];
        
        if (data['liked'] == true) {
            likeButton.className = "fa-solid fa-heart fa-2x";
        }
        else {
            likeButton.className  = "fa-regular fa-heart fa-2x";
        }
    })
    .catch((e) => alert('Sorry post can\'t be liked'));
    
}


function deleteComment(commentId) {
    const deleteItem = document.getElementById(`comment-text-${commentId}`);

    fetch(`/delete-comment/${commentId}`, {method: 'POST'})
    .then((res) => res.json())
    .then((data) => { console.log(data)
        
        if (data['commentLen'] == 0) {
            const options = document.getElementById(`options-${data['postId']}`);
            $(options).load(document.URL + ' ' + `#options-${data['postId']}`);
        }

        else if (data['success']) {
            const parentBox = document.getElementById(`comment-section-${data['postId']}`);
            $(deleteItem).remove();
            $(parentBox).load(document.URL+' '+ `#comment-section-${data['postId']}`);

        }
               
    }).catch((e) => alert('Sorry, can\'t delete this comment'));
   

}

 
function addComment(postId) {

    let searchData = new URLSearchParams()
    searchData.append('comment', document.getElementById(`comment-${postId}`).value); 
    console.log(document.getElementById(`comment-${postId}`).value);

    fetch(`/add-comment/${postId}`, {method: 'POST',
     body: searchData}).then((res) => res.json())
    .then((data) => { console.log(data)
        if (data['success']) {
            const commentDiv = document.getElementById(`form-reload-${data['postId']}`);
            
            $(commentDiv).load(document.URL + ' '+ `#form-reload-${data['postId']}`);
            
        }

    }).catch((e) => alert('Sorry, can\'t post this comment'));
    return false;
}



function deletePost(postId) {
    
    fetch(`/delete-post/${postId}`, {method: 'POST'}).then((res) => res.json())
    .then((data) => {
        console.log(data);
        if (data['success']) {
            const page = document.getElementById('posts-reload');
            $(page).load(document.URL + ' ' + '#posts-reload')
        }

    }).catch((e) => alert('Sorry, can\'t delete this post'));

}




