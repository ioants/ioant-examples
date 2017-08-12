import ioant.proto as proto
Import("env")

# proto.embedded_main(output_dir)
proto.embedded_main("lib/generated_proto/")
