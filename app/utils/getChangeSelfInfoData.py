
from app.models import User

def changeSelfInfo(username, formData, file):
    user = User.objects.get(username=username)
    user.address = formData['address']
    user.sex = formData['sex'] if formData['sex'] else ''
    if formData['textarea']:
        user.textarea = formData['textarea']
    if file.get('avatar') != None:
        user.avatar = file.get('avatar')

    user.save()

def changePassword(userInfo, passwordInfo):
    if not passwordInfo.get('oldPassword'):
        return '原始密码不能为空'
    if not passwordInfo.get('newPassword'):
        return '新密码不能为空'
    if not passwordInfo.get('newPasswordConfirm'):
        return '确认新密码不能为空'

    oldPwd = passwordInfo['oldPassword']
    newPwd = passwordInfo['newPassword']
    newPwdConfirm = passwordInfo['newPasswordConfirm']

    if oldPwd != userInfo.password:
        return '原始密码不正确'

    if newPwd != newPwdConfirm:
        return '两次新密码不一致'

    try:
        user = User.objects.get(username=userInfo.username)
    except User.DoesNotExist:
        return '用户不存在'

    user.password = newPwdConfirm
    user.save()
