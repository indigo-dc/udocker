all: 
	$(info > HTML pages being generated)
	cd templates && ./gen.sh
	$(info > Do not forget to customize the navbar.tmpl!)
clean:
	rm ./browser/*.html
	$(info > HTML pages deleted)
test: 	browser/lib/vizgrimoire.min.js
	$(info > Executing tests .. )
	cd test/jasmine; jasmine-headless-webkit -j jasmine.yml -c
	cd ../..

testci: browser/lib/vizgrimoire.min.js
	$(info > Executing tests .. )
	cd test/jasmine; xvfb-run jasmine-headless-webkit -j jasmine.yml -c
	cd ../..
