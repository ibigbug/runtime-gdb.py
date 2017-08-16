package main

import (
	"fmt"
	"net/http"
	_ "net/http/pprof"
	"os"
)

func main() {
	fmt.Println(os.Getpid())
	http.ListenAndServe(":9990", nil)
}
