# SwordSec backend task

## Kurulum

```bash
docker-compose up --build --scale rq-worker=5
```

## Protobufs

UsersService de iki ana methodumuz var

- SendUserInfo (unary - unary)
    - tek istek gönderip karşılığında tek cevap alıyoruz

- SendUserInfoClientStream (stream - unary)
    - çoğul istek gönderip karşılığında tek cevap alıyoruz


```proto
service Users {
    rpc SendUserInfo (UserRequest) returns (UserResponse);
    rpc SendUserInfoClientStream (stream UserRequest) returns (UserResponse);
}
```

İstemcinin çoğul istek göndermesi durumu da uygun geldi bana, bu yüzden onu da eklemke istedim.

ClientStream çoklu istekler üretip sunucuya gönderiyor ve sonucunda da tek cevap alıyor sunucudan.

Bizim de sunucuya kullanıcı verilerini göndereceğimizi hesaba katarak, kullanıcı veri akımı oluştura biliriz.


## İstemci

İstekleri oluşturduğumuz kısım burası oluyor
```py
def process_users_from_json_files():
    ...
    for user in json_content:
        yield UserRequest(**user)
    ...
```

burası da istekleri sunucuya gönderdiğimiz kısım
```py
def client_stream():
    users_client.SendUserInfo(
        process_users_from_json_files()
    )
```

Tamam, istemciden veri akımı yapmak iyi, hoş ama aslında birli methodu kullandım ana fonksiyon olarak


`main()` fonksiyonum 👇🏻

```py
def main():
    log.info("Client initialized...")
    for _user in process_users_from_json_files():
        ...
            user_response = users_client.SendUserInfo(
                _user
            )
        ...
```

her iki yöntem uygun bence, sadece projenin gereğine göre istediğimizi kullanabileceğimizi göstermek istedim.


## Sunucu

Bu kısımda sunucunun gelen isteklerle nasıl başa çıktığını gösteriyor


veri geldiği zaman `process_incoming_request()` fonksiyonunu parametresi ile birlikte kuyruğa ekliyoruz 

```py
def process_incoming_request(self, _data):

    self.data.update(
        MessageToDict(_data)
    )

    return UserResponse(status=True, message="ok")
```


```py
def SendUserInfo(self, request, context):
    log.info(f'incoming request -> {request}')
    q.enqueue(self.process_incoming_request, request)
```


istemciden veri akımı (client stream) yaptığımız zaman sunucuda durum farklı oluyor


bu zaman, kodun daha anlaşılır olması için isimlendirmeyi de `request` den `request_iterator` -e değiştirip, döngüye alıyoruz



```py
def SendUserInfoClientStream(self, request_iterator, context):

    for request in request_iterator:
        log.info(f'incoming request (client stream) -> {request}')

        q.enqueue(self.process_incoming_request, request)

    try:
        q.enqueue(self.write_to_json_file, file_name='all_users.json')

        return UserResponse(status=True, message="ok")
    except:
        return UserResponse(status=False, message="not ok")
```


gelen akımı kuyruğa ekledikten sonra `write_to_json_file()` methodunu çağırıp topladığımız verileri dosyaya kaydedebiliriz


burada özellikle dosyaya kaydetme methodunu da kuyruğa ekledim. çünkü bu methoda gelene kadar daha kuyruktaki işlemlerin bitmemesi ihtimali var. bu methodu da kuyruğa ekleyerek en sonda çalıştığından emin olabiliyoruz


## Docker dosyaları


Bu kısımda docker dosyalarını nasıl özelleştirdiğimi göstermek istiyorum.


genel olarak blog yazılarında böyle bir düzen görüyoruz, bu arada benimde docker dosyasının ilk halini aldığım yer burda [(real python)](https://realpython.com/python-microservices-grpc/#docker)



ama tabii ki bunu optimize edebiliriz..


neden projenin içeriğini kopyaladıktan sonra pip paketlerini kurmaya çalışıyoruz ki?


bu soruyu ilk kez kendime tutoriallardaki dokcer dosyalarının düzenini gördüğüm zaman vermiştim (django deploymenti daha yeni öğrendiğim zamanlarda)


projede herhangi nokta, harf bile değiştirsek tüm gereksinimleri yeniden kurmaya çalışacak



optimize ede bileceğimiz birşey, neden boşuna zamanımızı çalsın ki? hem docker bizim için keş sistemi kurdu o kadar. niye değerlendirmiyoruz?



en azından ben değerlendirmeye çalıştım..


#### varsayılan docker dosyası

```Dockerfile
FROM python:3.8-slim

RUN mkdir /service

# COPY protobufs/ /service/protobufs/
COPY . /service/client/

WORKDIR /service/client

RUN pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I protobufs --python_out=. \
           --grpc_python_out=. protobufs/users.proto


EXPOSE 50051
ENTRYPOINT [ "python", "client.py" ]
```

#### özelleştirdiğim docker dosyası

```Dockerfile
...

RUN mkdir /service
WORKDIR /service/client


COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .

...
```


görüyor musunuz? projenin içeriğini en sonda kopyalıyoruz docker container-e, gereksinimleri kurduktan sonra. şimdi herhangi bir değişiklik yapsak bile (requirements dışında) keş kullanılacak, gereksinimler yeniden kurulmayacak.


aslında bu esnada bi' kahve içebilirdik ama.. neyse artık kahve falan yok bize..



## Docker-compose

[docker-compose](./docker-compose.yml) dosyamızda pek açıklanacak birşey yok aslında, sadece worker kısmını göstermek istiyorum


iki seçim koydum, ya python ile çalıştıracağız worker modülünü 


YA DA


docker hub-dan (umarız ki güvendiğimiz birinden) hazır imajı kullanarak


```yml
worker:
    build: worker # ./worker
    networks:
        - microservices
    environment:
        - REDIS_HOST=redis
        - REDIS_PORT=6379
    depends_on:
        - server
        - redis

    #  OR 👇🏻

    rq-worker:
        image: jaredv/rq-docker:0.0.2
        command: rq worker -u redis://redis:6379 high normal low

        networks:
            - microservices

        depends_on:
            - redis

    rq-dashboard:
        image: jaredv/rq-docker:0.0.2 
        command: rq-dashboard -H rq-server
        ports:
        - 9181:9181
        
        networks:
            - microservices

        depends_on:
            - redis
```

kuyruğu gözlemlemek istemeğimizi ihtimale alarak `rq-dashboard` da ekledim,


en sonda da, bu servislerin sıralamasını nasıl kurduğumu göstermek istiyorum. redis serveri en sonda başlatmak istemeyiz, değil mi?


- redis (sunucu)
- gRPC sunucu (redis sunucusundan asılıdır)
- gRPC client (gRPC sunucusundan asılıdır)
- python redis queue worker (hem gRPC hem de redis sunucusundan asılıdır)
- rq-dashboard (redis sunucusundan asılıdır)



Projeyle ilgili herhangi bir sorunuz olursa da -> [mirkanan.k@labrin.tech](mailto:mirkanan.k@labrin.tech)