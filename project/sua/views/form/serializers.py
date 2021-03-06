from django.contrib.auth.models import User
from project.sua.models import Student, Sua, Application, Activity, Publicity, Appeal, Proof

from rest_framework import serializers

from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate


class AddUserSerializer(serializers.HyperlinkedModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'}, default='12345678', write_only=True)

    class Meta:
        model = User
        fields = ('password', )


class AddStudentSerializer(serializers.HyperlinkedModelSerializer):
    user = AddUserSerializer()

    class Meta:
        model = Student
        fields = ('url', 'number', 'name', 'suahours', 'grade', 'classtype', 'phone', 'user', 'id','power')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(
            username=validated_data['number'],
            password=make_password(user_data['password']),
        )
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user
        user.set_password(user_data['password'])
        user.save()
        instance.number = validated_data.get('number',instance.number)
        instance.name = validated_data.get('name',instance.name)
        instance.suahours = validated_data.get('suahours',instance.suahours)
        instance.grade = validated_data.get('grade',instance.grade)
        instance.classtype = validated_data.get('classtype',instance.classtype)
        instance.phone = validated_data.get('phone',instance.phone)
        instance.id = validated_data.get('id',instance.id)
        instance.power = validated_data.get('power',instance.power)
        instance.save()
        return instance


class ActivityWithSuaSerialiezer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Activity
        fields = ('url','title','date','group','owner','is_created_by_student')


class AddSuaSerializer(serializers.HyperlinkedModelSerializer):
    student = AddStudentSerializer()
    activity = ActivityWithSuaSerialiezer()

    class Meta:
        model = Sua
        fields = ('url', 'activity', 'student', 'team', 'suahours', 'id','is_valid')

class AddActivitySerializer(serializers.HyperlinkedModelSerializer):
    suas = AddSuaSerializer(
        many=True,
        source='get_suas_all',
        read_only=True
    )

    class Meta:
        model = Activity
        fields = ('url', 'title', 'detail', 'group', 'date','suas', 'id','is_valid')

    def create(self, validated_data):
        print(validated_data)
        sua_datas = []
        if 'suas' in validated_data:
            sua_datas = validated_data.pop('suas')
        owner = validated_data['owner']
        if owner.is_staff or owner.student.power == 1:
            activity = Activity.objects.create(is_created_by_student=False,**validated_data)
        else:
            activity = Activity.objects.create(is_created_by_student=True,**validated_data)
        for sua_data in sua_datas:
            sua = Sua.objects.create(owner=owner, activity=activity, **sua_data)
        return activity
    def update(self, instance, validated_data):
        sua_datas = []
        if 'suas' in validated_data:
            sua_datas = validated_data.pop('suas')
        suas = (instance.suas).all()
        suas = list(suas)
        instance.title = validated_data.get('title',instance.title)
        instance.detail = validated_data.get('detail',instance.detail)
        instance.group = validated_data.get('group',instance.group)
        instance.date = validated_data.get('date',instance.date)
        instance.id = validated_data.get('id',instance.id)
        instance.save()

        for sua_data in sua_datas:
            sua = suas.pop(0)
            sua.activity = sua_data.get('activity', sua.activity)
            sua.student = sua_data.get('student', sua.student)
            sua.team = sua_data.get('team', sua.team)
            sua.suahours = sua_data.get('suahours', sua.suahours)
            sua.save()
        return instance


class PublicityWithAppealSerializer(serializers.HyperlinkedModelSerializer):
    activity = AddActivitySerializer()

    class Meta:
        model = Activity
        fields = ('url','activity','title')

class AddAppealSerializer(serializers.HyperlinkedModelSerializer):
    student = AddStudentSerializer()
    publicity = PublicityWithAppealSerializer()

    class Meta:
        model = Appeal
        fields = ('url','owner','student','publicity', 'content', 'status', 'is_checked', 'feedback','created', 'id')


class AddPublicitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Publicity
        fields = ('url','owner','activity', 'title', 'content', 'contact', 'is_published', 'begin', 'end', 'id')


class AddProofSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Proof
        fields = ('url', 'is_offline', 'proof_file')

    def is_valid(self, *args, **kwargs):
        is_valid_super = super(AddProofSerializer, self).is_valid(*args, **kwargs)
        has_upload_file = True if 'proof_file' in self.validated_data.keys() else False
        is_offline = True if self.validated_data['is_offline'] else False
        return is_valid_super and (has_upload_file or is_offline)


class AddApplicationSerializer(serializers.HyperlinkedModelSerializer):
    sua = AddSuaSerializer()
    proof = AddProofSerializer()

    class Meta:
        model = Application
        fields = ('url', 'sua', 'created','contact', 'proof','feedback', 'id','is_checked','status')


    def create(self, validated_data):
        owner = validated_data['owner']
        sua_data = validated_data.pop('sua')
        sua = Sua.objects.create(owner=owner, **sua_data)
        proof_data = validated_data.pop('proof')
        proof = Proof.objects.create(owner=owner, **proof_data)
        application = Application.objects.create(sua=sua, proof=proof,**validated_data)
        return application

    def update(self, instance, validated_data):
        proof_data = validated_data.pop('proof')
        proof = instance.proof
        proof.save()
        sua_datas = validated_data.pop('sua')
#        sua = (instance.sua).all()
        sua = instance.sua
        sua.save()
        instance.create = validated_data.get('created',instance.created)
        instance.contact = validated_data.get('contact',instance.contact)
        instance.id = validated_data.get('id',instance.id)
        instance.save()
        return instance

class detailofstudentSerializer(serializers.HyperlinkedModelSerializer):
    suas = AddSuaSerializer(
        many=True,
        source='get_suas'
    )
    user = AddUserSerializer()

    class Meta:
        model = Student
        fields = ('url', 'number', 'name', 'suahours', 'grade', 'classtype', 'phone', 'user', 'id','suas','power')
