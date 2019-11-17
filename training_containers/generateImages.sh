
for counter in {1..20};do
	docker build . -f docker/svm/Dockerfile -t matoran/lauzhack_svm --no-cache > /dev/null

	docker push matoran/lauzhack_svm | tail -n 1
done