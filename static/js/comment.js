document.addEventListener('DOMContentLoaded', function() {
    console.log('评论功能初始化开始');
    
    const commentForm = document.getElementById('commentForm');
    if (!commentForm) {
        console.error('未找到评论表单元素');
        return;
    }

    const scoreSelect = document.getElementById('score');
    const contentTextarea = document.getElementById('content');
    const submitButton = document.querySelector('#commentForm button[type="submit"]');

    if (!scoreSelect || !contentTextarea || !submitButton) {
        console.error('未找到评论表单的必要元素');
        return;
    }

    commentForm.addEventListener('submit', function(e) {
        console.log('评论表单提交事件触发');

        try {
            if (!scoreSelect.value) {
                e.preventDefault();
                alert('请选择评分');
                return false;
            }

            if (!contentTextarea.value.trim()) {
                e.preventDefault();
                alert('请输入评论内容');
                return false;
            }

            console.log('评论验证通过，准备提交');
            return true;
        } catch (error) {
            console.error('评论提交验证失败:', error);
            e.preventDefault();
            return false;
        }
    });
    
    console.log('评论功能初始化完成');
});