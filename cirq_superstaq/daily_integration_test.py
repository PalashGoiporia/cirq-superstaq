"""Integration checks that run daily (via Github action) between client and prod server."""

import os
import textwrap

import cirq
import pytest
from applications_superstaq import SuperstaQException

import cirq_superstaq


@pytest.fixture
def service() -> cirq_superstaq.Service:
    token = os.getenv("TEST_USER_TOKEN")
    service = cirq_superstaq.Service(api_key=token)
    return service


def test_ibmq_compile(service: cirq_superstaq.Service) -> None:
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq_superstaq.AceCRPlusMinus(qubits[0], qubits[1]))
    out = service.ibmq_compile(circuit, target="ibmq_jakarta_qpu")
    assert isinstance(out.circuit, cirq.Circuit)
    assert 800 <= out.pulse_sequence.duration <= 1000  # 896 as of 12/27/2021
    assert out.pulse_sequence.start_time == 0
    assert len(out.pulse_sequence) == 5


def test_acer_non_neighbor_qubits_compile(service: cirq_superstaq.Service) -> None:
    qubits = cirq.LineQubit.range(4)
    circuit = cirq.Circuit(
        cirq_superstaq.AceCRMinusPlus(qubits[0], qubits[1]),
        cirq_superstaq.AceCRMinusPlus(qubits[1], qubits[2]),
        cirq_superstaq.AceCRMinusPlus(qubits[2], qubits[3]),
    )

    out = service.ibmq_compile(circuit, target="ibmq_bogota_qpu")
    assert isinstance(out.circuit, cirq.Circuit)
    assert 5700 <= out.pulse_sequence.duration <= 7500  # 7424 as of 4/06/2022
    assert out.pulse_sequence.start_time == 0
    assert len(out.pulse_sequence) == 67


def test_aqt_compile(service: cirq_superstaq.Service) -> None:
    qubits = cirq.LineQubit.range(8)
    circuit = cirq.Circuit(cirq.H(qubits[4]))

    cirq.testing.assert_circuits_with_terminal_measurements_are_equivalent(
        service.aqt_compile(circuit).circuit, circuit, atol=1e-08
    )

    compiled_circuits = service.aqt_compile([circuit]).circuits
    assert isinstance(compiled_circuits, list)
    for compiled_circuit in compiled_circuits:
        cirq.testing.assert_circuits_with_terminal_measurements_are_equivalent(
            compiled_circuit, circuit, atol=1e-08
        )
    compiled_circuits = service.aqt_compile([circuit, circuit]).circuits

    assert isinstance(compiled_circuits, list)
    for compiled_circuit in compiled_circuits:
        cirq.testing.assert_circuits_with_terminal_measurements_are_equivalent(
            compiled_circuit, circuit, atol=1e-08
        )


def test_get_balance(service: cirq_superstaq.Service) -> None:
    balance_str = service.get_balance()
    assert isinstance(balance_str, str)
    assert balance_str.startswith("$")

    assert isinstance(service.get_balance(pretty_output=False), float)


def test_ibmq_set_token() -> None:
    api_token = os.environ["TEST_USER_TOKEN"]
    ibmq_token = os.environ["TEST_USER_IBMQ_TOKEN"]
    service = cirq_superstaq.Service(api_key=api_token)
    assert service.ibmq_set_token(ibmq_token) == "Your IBMQ account token has been updated"

    with pytest.raises(SuperstaQException, match="IBMQ token is invalid."):
        assert service.ibmq_set_token("INVALID_TOKEN")


def test_tsp(service: cirq_superstaq.Service) -> None:
    cities = ["Chicago", "San Francisco", "New York City", "New Orleans"]
    out = service.tsp(cities)
    for city in cities:
        assert city.replace(" ", "+") in out.map_link[0]


def test_get_backends(service: cirq_superstaq.Service) -> None:
    result = service.get_backends()
    assert "ibmq_qasm_simulator" in result["compile-and-run"]
    assert "aqt_keysight_qpu" in result["compile-only"]


def test_qscout_compile(service: cirq_superstaq.Service) -> None:
    q0 = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.H(q0), cirq.measure(q0))
    compiled_circuit = cirq.Circuit(
        cirq.PhasedXPowGate(phase_exponent=-0.5, exponent=0.5).on(q0),
        cirq.Z(q0) ** -1.0,
        cirq.measure(q0),
    )

    jaqal_program = textwrap.dedent(
        """\
        register allqubits[1]

        prepare_all
        R allqubits[0] -1.5707963267948966 1.5707963267948966
        Rz allqubits[0] -3.141592653589793
        measure_all
        """
    )
    out = service.qscout_compile(circuit)
    cirq.testing.assert_circuits_with_terminal_measurements_are_equivalent(
        out.circuit, compiled_circuit, atol=1e-08
    )
    assert out.jaqal_program == jaqal_program


def test_cq_compile(service: cirq_superstaq.Service) -> None:
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]), cirq.measure(qubits[0])
    )

    out = service.cq_compile(circuit)
    cirq.testing.assert_circuits_with_terminal_measurements_are_equivalent(
        out.circuit, circuit, atol=1e-08
    )


def test_get_aqt_configs(service: cirq_superstaq.Service) -> None:
    res = service.aqt_get_configs()
    assert "pulses" in res
    assert "variables" in res
